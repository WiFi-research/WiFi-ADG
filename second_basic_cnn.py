import tensorflow as tf
import net_element as ne
from decorator2 import lazy_property


class SecondBasicCnn:
    """
    A cnn for mnist dataset with following structure:

    data[None, 28, 28, 1]
    max_pooling(relu(conv[5, 5, 1, 32]))
    max_pooling(relu(conv[5, 5, 32, 64]))
    drop_out(fc[7*7*64, 1024])
    softmax(fc[1024, 10])
    """
    def __init__(self, data, groundtruth, p_keep):
        self.data = tf.reshape(data, [-1, 20, 90, 1])
        self.groundtruth = groundtruth
        self.p_keep = p_keep
        self.weights
        self.biases
        self.prediction
        self.optimization
        self.accuracy

    @lazy_property
    def weights(self):
        _weights = {
            'W_conv1': ne.weight_variable([3, 9, 1, 16], name='W_conv1'),
            'W_conv2': ne.weight_variable([2, 8, 16, 32], name='W_conv2'),
            'W_conv3': ne.weight_variable([3, 6, 32, 64], name='W_conv3'),
            'W_fc1': ne.weight_variable([1 * 6 * 64, 128], name='W_fc1'),
            'W_fc2': ne.weight_variable([128, 10], name='W_fc2')
        }
        return _weights

    @lazy_property
    def biases(self):
        _biases = {
            'b_conv1': ne.bias_variable([16], name='b_conv1'),
            'b_conv2': ne.bias_variable([32], name='b_conv2'),
            'b_conv3': ne.bias_variable([64], name='b_conv3'),
            'b_fc1': ne.bias_variable([128], name='b_fc1'),
            'b_fc2': ne.bias_variable([10], name='b_fc2')
        }
        return _biases

    @lazy_property
    def prediction(self):
        """
        The structure of the network.
        """
        h_conv1 = tf.nn.relu(
            ne.conv2d_valid(
                self.data, self.weights['W_conv1']
            ) + self.biases['b_conv1']
        )
        h_pool1 = ne.max_pool_2x2(h_conv1)

        h_conv2 = tf.nn.relu(
            ne.conv2d_valid(
                h_pool1, self.weights['W_conv2']
            ) + self.biases['b_conv2']
        )
        h_pool2 = ne.max_pool_2x2(h_conv2)
        
        h_conv3 = tf.nn.relu(
            ne.conv2d_valid(
                h_pool2, self.weights['W_conv3']
            ) + self.biases['b_conv3']
        )
        h_pool3 = ne.max_pool_2x2(h_conv3)

        h_pool3_flat = tf.reshape(h_pool3, [-1, 1*6*64])
        
        h_fc1 = tf.nn.relu(
            tf.matmul(
                h_pool3_flat, self.weights['W_fc1']
            ) + self.biases['b_fc1']
        )

        h_fc1_drop = tf.nn.dropout(h_fc1, self.p_keep)
        h_fc2 = tf.matmul(h_fc1_drop, self.weights['W_fc2']) + \
            self.biases['b_fc2']
        y_conv = tf.nn.softmax(h_fc2)

        return y_conv

    @lazy_property
    def optimization(self):
        logprob = tf.log(self.prediction + 1e-12)
        cross_entropy = -tf.reduce_sum(self.groundtruth * logprob)
        optimizer = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
        return optimizer

    @lazy_property
    def accuracy(self):
        correct_prediction = tf.equal(
            tf.argmax(self.groundtruth, 1),
            tf.argmax(self.prediction, 1)
        )
        acc = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
        return acc

    def load(self, sess, path, name='cnn_per.ckpt'):
        """
        Load trained model from .ckpt file.
        """
        saver = tf.train.Saver(dict(self.weights, **self.biases))
        saver.restore(sess, path+'/'+name)

    def save(self, sess, path, name='cnn_per.ckpt'):
        """
        Save trained model to .ckpt file.
        """
        saver = tf.train.Saver(dict(self.weights, **self.biases))
        saver.save(sess, path+'/'+name)
