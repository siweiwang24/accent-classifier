"""
Train model on data. Evaluate test set on best models.

Copyright 2021. Siwei Wang.
"""
from typing import Dict, List
from pickle import dump
from matplotlib import pyplot as plt  # type: ignore
from tensorflow.keras import optimizers, callbacks  # type: ignore
from click import command, option  # type: ignore
from preprocess import dataset_class_weights, load_accents
from util import ACCENTS, hyperparameters, data_shape, get_model
# pylint: disable=redefined-outer-name,no-value-for-parameter


def plot_history(history: Dict[str, List[int]],
                 metrics: List[str], model_name: str, dpi: int):
    """Plot training and validation metrics and loss."""
    for metric in metrics + ['loss']:
        plt.figure(dpi=dpi)
        plt.plot(history[metric])
        plt.plot(history[f'val_{metric}'])
        plt.legend([metric, f'val_{metric}'])
        plt.xlabel('Epoch')
        plt.ylabel(f'{metric.capitalize()} Value')
        plt.title(f'{metric.capitalize()} over Training')
        plt.savefig(f'{model_name}_{metric}.png')


@command()
@option('--architecture', '-a', type=str, required=True,
        help='Choose one of "bilstm", "cnn", or "cnn_bilstm"')
def train(architecture: str):
    """Train model on data. Evaluate test set on best models."""
    hyp = hyperparameters()
    train, val, test = [ds.repeat().shuffle(hyp['shuffle_buffer'])
                        .batch(hyp['batch_size'], drop_remainder=True)
                        .prefetch(1)
                        for ds in load_accents(hyp)]
    in_shape = data_shape(train)

    tracked_metrics = ['accuracy']
    model = get_model(architecture, in_shape, len(ACCENTS))
    model.build(in_shape)
    model.compile(optimizer=optimizers.Nadam(hyp['learning_rate']),
                  loss='sparse_categorical_crossentropy',
                  metrics=tracked_metrics)
    model.summary()

    checkpoints = [callbacks.ModelCheckpoint(f'{model.name}_{met}.hdf5',
                                             monitor=f'val_{met}',
                                             save_best_only=True)
                   for met in tracked_metrics + ['loss']]
    weights = dataset_class_weights(ACCENTS)
    hist = model.fit(train, epochs=hyp['epochs'], class_weight=weights,
                     steps_per_epoch=hyp['train_steps'], callbacks=checkpoints,
                     validation_data=val, validation_steps=hyp['val_steps'],
                     workers=hyp['cpu_cores'], use_multiprocessing=True)

    assert hist is not None
    with open(f'{model.name}_history.pickle', 'wb') as pick:
        dump(hist.history, pick)
    dpi = hyp['plot_dpi']
    assert isinstance(dpi, int)
    plot_history(hist.history, tracked_metrics, model.name, dpi)
    for met in tracked_metrics + ['loss']:
        print(f'Evaluating {model.name} with best {met}...')
        model.load_weights(f'{model.name}_{met}.hdf5')
        model.evaluate(test, steps=hyp['test_steps'])


if __name__ == '__main__':
    train()
