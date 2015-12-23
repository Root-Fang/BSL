# -*- coding: utf-8 -*-
import kombu
from eventlet import pools, semaphore
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
                msg = dict()
                callback(msg)#回调函数处理该msg
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
        options = {'durable': False,#是否持久
                   'auto_delete': False,#自动删除，即如果最后一个消费者断开的时候是不是会自动删除队列
                   'exclusive': False}#只有创建这个队列的消费者程序才允许连接到该队列。这种队列对于这个消费者程序是私有的
        options.update(kwargs)
        exchange_name = exchange_name
        exchange = kombu.entity.Exchange(name=exchange_name,
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
    def __init__(self, conf, name, **kwargs):
        self.conf = conf
        self.service_name = name
        node = getattr(conf, name)
        self.exchange_name = node['exchange']
        self.topic = node['topic']
        self.consumers = []
        self.channel = None
    def create_channel(self):
        pass
    def create_consumer(self):
        self.consumers.append(TopicConsumer(0, self.topic, 1, len(self.consumers), self.exchange_name))
    def consume_in_thread(self):
        pass