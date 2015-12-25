# -*- coding: utf-8 -*-
import kombu, eventlet
from eventlet import pools, semaphore, greenlet
class ConsumerBase(object):
    """Consumer base class."""

    def __init__(self, channel, callback, tag, **kwargs):
        """Declare a queue on an amqp channel.

        'channel' is the amqp channel to use
        'callback' is the callback to call when messages are received
        'tag' is a unique ID for the consumer on the channel

        queue name, exchange name, and other kombu options are
        passed in here as a dictionary.
        """
        self.callback = callback
        self.tag = str(tag)
        self.kwargs = kwargs
        self.queue = None
        self.reconnect(channel)

    def reconnect(self, channel):
        """Re-declare the queue after a rabbit reconnect"""
        self.channel = channel
        self.kwargs['channel'] = channel
        self.queue = kombu.entity.Queue(**self.kwargs)#若参数值含有Exchange，那么会直接绑定上去
        self.queue.declare()

    def consume(self, *args, **kwargs):
        """Actually declare the consumer on the amqp channel.  This will
        start the flow of messages from the queue.  Using the
        Connection.iterconsume() iterator will process the messages,
        calling the appropriate callback.

        If a callback is specified in kwargs, use that.  Otherwise,
        use the callback passed during __init__()

        If kwargs['nowait'] is True, then this call will block until
        a message is read.   这里解释有误，True不等待server的响应信息

        参数noack : If enabled the broker will automatically ack messages.

        Messages will automatically be acked if the callback doesn't
        raise an exception
        """

        options = {'consumer_tag': self.tag}
        options['nowait'] = kwargs.get('nowait', False)
        callback = kwargs.get('callback', self.callback)
        if not callback:
            raise ValueError("No callback defined")

        def _callback(raw_message):
            message = self.channel.message_to_python(raw_message)#将消息解码成python能识别的值
            try:
                # msg = rpc_common.deserialize_msg(message.payload)#payload是已经解码的消息
                callback(message.payload)#回调函数处理该msg
            except Exception:
                pass
            finally:
                message.ack()#Acknowledge this message as being processed., This will remove the message from the queue.

        self.queue.consume(*args, callback=_callback, **options)#Start a queue consumer   consume(consumer_tag='', callback=None, no_ack=None, nowait=False)

    def cancel(self):
        """Cancel the consuming from the queue, if it has started"""
        try:
            self.queue.cancel(self.tag)
        except KeyError, e:
            # NOTE(comstud): Kludge to get around a amqplib bug
            if str(e) != "u'%s'" % self.tag:
                raise
        self.queue = None

class TopicConsumer(ConsumerBase):
    """Consumer class for 'topic'"""

    def __init__(self, channel, topic, callback, tag,
                 exchange_name=None, **kwargs):
        """Init a 'topic' queue.

        :param channel: the amqp channel to use
        :param topic: the topic to listen on
        :paramtype topic: str
        :param callback: the callback to call when messages are received
        :param tag: a unique ID for the consumer on the channel
        :param name: optional queue name, defaults to topic
        :paramtype name: str

        Other kombu options may be passed as keyword arguments
        """
        # Default options
        options = {'durable': True,#是否持久
                   'auto_delete': False,#自动删除，即如果最后一个消费者断开的时候是不是会自动删除队列
                   'exclusive': False}#只有创建这个队列的消费者程序才允许连接到该队列。这种队列对于这个消费者程序是私有的
        options.update(kwargs)
        exchange_name = exchange_name
        exchange = kombu.Exchange(name=exchange_name,
                                         type='topic',
                                         durable=options['durable'],
                                         auto_delete=options['auto_delete'])
        super(TopicConsumer, self).__init__(channel,
                                            callback,
                                            tag,
                                            name=topic,
                                            exchange=exchange,
                                            routing_key=topic,
                                            **options)

class Pool(pools.Pool):
    def __init__(self, conf, connection_cls, **kwargs):
        self.connection_cls = connection_cls
        self.kwargs = kwargs
        self.conf = conf
        max_size = conf.get('pool_size', 'rabbitmq', default=128)
        super(Pool, self).__init__(max_size = max_size)
    def create(self):
        return self.connection_cls(self.conf, **self.kwargs)

_pool_create_sem = semaphore.Semaphore()


def get_connection_pool(conf, connection_cls):
    with _pool_create_sem:
        # Make sure only one thread tries to create the connection pool.
        if not connection_cls.pool:
            connection_cls.pool = Pool(conf, connection_cls)
    return connection_cls.pool


class ConnectionContext(object):
    def __init__(self, conf, connection_pool, pooled=True, **kwargs):
        self.connection = None
        self.connection_pool = connection_pool
        self.pooled = pooled
        self.conf = conf
        self.kwargs = kwargs
        if self.pooled:
            self.connection = self.connection_pool.get()
        else:
            self.connection = self.connection_pool.connection_cls(conf, **kwargs)
    def __getattr__(self, key):
        try:
            return getattr(self.connection, key)
        except Exception as e:
            raise e
    def _done(self):
        if self.pooled:
            self.connection.reset()
            self.connection_pool.put(self.connection)
        else:
            self.connection.reset()
        self.connection = None
    def close(self):
        self._done()

class Connection(object):
    pool = None
    def __init__(self, conf, **kwargs):
        self.conf = conf
        self.exchange_name = conf.get('exchange_name', 'rabbitmq', default='MR')
        self.consumers = []
        self.connection = None
        self.consume_thread = None
        self.reconnect()
    def reconnect(self):
        if self.connection:
            self.reset()
        self.connection = kombu.Connection(self.conf.get('url', 'rabbitmq'))
        try:
            self.connection.connect()
            self.channel = self.connection.channel()
        except Exception as e:
            raise e
    def create_consumer(self, topic, callback):
        self.consumers.append(TopicConsumer(self.channel, topic, callback, len(self.consumers), self.exchange_name))
    def consume_in_thread(self):
        def _start():
            for consumer in self.consumers:
                consumer.consume()
            while True:
                self.connection.drain_events()
        greenthread = eventlet.spawn(_start)
        self.consume_thread = greenthread
    def reset(self):
        if self.consume_thread is not None:
            self.consume_thread.kill()
            try:
                self.consume_thread.wait()
            except greenlet.GreenletExit:
                pass
        if len(self.consumers):
            for consumer in self.consumers:
                consumer.cancel()
        self.consume_thread = None
        self.consumers = []

def wait(conn):
    try:
        conn.consume_thread.wait()
    except greenlet.GreenletExit:
        pass

def callback(msg):
    print msg

if __name__ == "__main__":
    from configure import CONF
    path = "../etc/bsl.conf"
    CONF.setup(path)
    get_connection_pool(CONF, Connection)
    conn = ConnectionContext(CONF, Connection.pool)
    conn.create_consumer('MRtest', callback)
    conn.consume_in_thread()
    conn.close()
    conn1 = ConnectionContext(CONF, Connection.pool)
    conn1.create_consumer('MRtest', callback)
    conn1.consume_in_thread()
    wait(conn1)
    #wait(conn)
    # from eventlet import sleep
    # lst = []
    # eventlet.monkey_patch(all=True)
    # def printf(content):
    #     print content
    #     sleep(1)
    # def func(count):
    #     for i in range(count):
    #         lst.append(eventlet.spawn(printf, "index = " + str(i)))
    # def wrap(func, count):
    #     green = eventlet.spawn(func, count)
    #     green.wait()
    #     print "wrap done"
    # green = eventlet.spawn(wrap, func, 10)
    # green.wait()



