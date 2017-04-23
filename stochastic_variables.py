

import tensorflow as tf
from tensorflow.contrib.rnn import BasicLSTMCell, LSTMStateTuple

from tensorflow.contrib.rnn.python.ops.core_rnn_cell_impl import _checked_scope


def get_random_normal_variable(name, mean, standard_dev, shape, dtype):

    """
    A wrapper around tf.get_variable which lets you get a "variable" which is
     explicitly a sample from a normal distribution.
    """
    mean = tf.get_variable(name + "_mean", shape,
                           initializer=tf.constant_initializer(mean),
                           dtype=dtype)
    standard_deviation = tf.get_variable(name + "_standard_deviation", shape,
                                         initializer=tf.constant_initializer(standard_dev),
                                         dtype=dtype)
    weights = mean + (standard_deviation * tf.random_normal(shape, 0.0, 1.0, dtype))
    return weights, mean, standard_deviation


class ExternallyParameterisedLSTM(BasicLSTMCell):
    """
    A simple extension of an LSTM in which the weights are passed in to the class,
    rather than being automatically generated inside the cell when it is called.
    This allows us to parameterise them in other, funky ways.
    """

    def __init__(self, weight, bias, **kwargs):
        self.weight = weight
        self.bias = bias
        super(ExternallyParameterisedLSTM, self).__init__(**kwargs)

    def __call__(self, inputs, state, scope=None):
        """Long short-term memory cell (LSTM)."""
        with _checked_scope(self, scope or "basic_lstm_cell", reuse=self._reuse):
            # Parameters of gates are concatenated into one multiply for efficiency.
            if self._state_is_tuple:
                c, h = state
            else:
                c, h = tf.split(value=state, num_or_size_splits=2, axis=1)

            all_inputs = tf.concat([inputs, h], 1)

            concat = tf.nn.bias_add(tf.matmul(all_inputs, self.weight), self.bias)

            # i = input_gate, j = new_input, f = forget_gate, o = output_gate
            i, j, f, o = tf.split(value=concat, num_or_size_splits=4, axis=1)

            new_c = (c * tf.sigmoid(f + self._forget_bias) + tf.sigmoid(i) *
                     self._activation(j))
            new_h = self._activation(new_c) * tf.sigmoid(o)

            if self._state_is_tuple:
                new_state = LSTMStateTuple(new_c, new_h)
            else:
                new_state = tf.concat([new_c, new_h], 1)
            return new_h, new_state
