"""
Model definitions and getters.

Copyright 2021. Siwei Wang.
"""
from typing import List, Tuple
import tensorflow as tf  # type: ignore
from tensorflow.keras import Model, Sequential, layers  # type: ignore
from tensorflow.keras.regularizers import l1_l2  # type: ignore
from tensorflow.keras.initializers import LecunNormal  # type: ignore


def _conv_layer(filters: int, kernel_sz: int) -> layers.Conv2D:
    """Create a regularized Conv2D layer."""
    return layers.Conv2D(filters, kernel_sz, padding='same',
                         activation='selu',
                         kernel_initializer=LecunNormal(),
                         kernel_regularizer=l1_l2(0.02, 0.03))


def _lstm_layer(units: int, ret_seq: bool) -> layers.LSTM:
    """Create a regularized LSTM layer."""
    return layers.LSTM(units, return_sequences=ret_seq,
                       kernel_regularizer=l1_l2(0.02, 0.03),
                       recurrent_regularizer=l1_l2(0.02, 0.03),
                       bias_regularizer=l1_l2(0.02, 0.03),
                       dropout=0.2, recurrent_dropout=0.4)


def _global_depth_pool(pool_op: str) -> layers.Lambda:
    """Global (avg or max) depth pooling and reshape."""
    assert pool_op in ('avg', 'max')
    func = tf.reduce_mean if pool_op == 'avg' else tf.reduce_max
    return layers.Lambda(lambda tensor: func(tensor, axis=-1),
                         name=f'global_depth_{pool_op}_pool')


def _cnn_layers(in_shape: Tuple[int, ...]) -> List[layers.Layer]:
    """Get a list of layers for CNN without final predictor."""
    return [layers.Reshape((*in_shape, 1), input_shape=in_shape),
            _conv_layer(32, 5),
            layers.MaxPool2D(pool_size=(1, 2)),
            _conv_layer(64, 3),
            layers.MaxPool2D(pool_size=(1, 2)),
            _conv_layer(64, 3),
            _global_depth_pool('max')]


def _lstm_layers(num_labels: int) -> List[layers.Layer]:
    """Get a list of layers for LSTM with final predictor."""
    return [layers.Bidirectional(_lstm_layer(36, True)),
            layers.Bidirectional(_lstm_layer(36, True)),
            layers.Bidirectional(_lstm_layer(36, False)),
            layers.Dense(num_labels, activation='softmax')]


def get_cnn(in_shape: Tuple[int, ...], num_labels: int) -> Model:
    """Define and retrieve CNN model."""
    return Sequential(
        layers=_cnn_layers(in_shape) + [
            layers.Flatten(),
            layers.Dense(num_labels, activation='softmax')
        ],
        name='cnn')


def get_bilstm(num_labels: int) -> Model:
    """Define and retrieve BiLSTM model."""
    return Sequential(
        layers=_lstm_layers(num_labels),
        name='bilstm')


def get_cnn_bilstm(in_shape: Tuple[int, ...],
                   num_labels: int) -> Model:
    """Define and retrive CNN_BiLSTM model."""
    return Sequential(
        layers=_cnn_layers(in_shape) + _lstm_layers(num_labels),
        name='cnn_bilstm')
