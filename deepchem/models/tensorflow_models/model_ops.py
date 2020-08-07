#"""Ops for graph construction."""
#from __future__ import print_function
#from __future__ import division
#from __future__ import unicode_literals
#
#import sys
#import traceback
#import tensorflow as tf
#from keras import backend as K
#
#def cosine_distances(test, support):
#  """Computes pairwise cosine distances between provided tensors
#
#  Parameters
#  ----------
#  test: tf.Tensor
#    Of shape (n_test, n_feat)
#  support: tf.Tensor
#    Of shape (n_support, n_feat)
#
#  Returns
#  -------
#  tf.Tensor:
#    Of shape (n_test, n_support)
#  """
#  rnorm_test = tf.rsqrt(tf.reduce_sum(tf.square(test), 1,
#                     keep_dims=True)) + K.epsilon()
#  rnorm_support = tf.rsqrt(tf.reduce_sum(tf.square(support), 1,
#                           keep_dims=True)) + K.epsilon()
#  test_normalized = test * rnorm_test
#  support_normalized = support * rnorm_support
#
#  # Transpose for mul
#  support_normalized_t = tf.transpose(support_normalized, perm=[1,0])  
#  g = tf.matmul(test_normalized, support_normalized_t)  # Gram matrix
#  return g
#
#def euclidean_distance(test, support, max_dist_sq=20):
#  """Computes pairwise euclidean distances between provided tensors
#
#  TODO(rbharath): BROKEN! THIS DOESN'T WORK!
#
#  Parameters
#  ----------
#  test: tf.Tensor
#    Of shape (n_test, n_feat)
#  support: tf.Tensor
#    Of shape (n_support, n_feat)
#  max_dist_sq: float, optional
#    Maximum pairwise distance allowed.
#
#  Returns
#  -------
#  tf.Tensor:
#    Of shape (n_test, n_support)
#  """
#  test = tf.expand_dims(test, 1)
#  support = tf.expand_dims(support, 0)
#  g = -tf.maximum(tf.reduce_sum(tf.square(test - support), 2), max_dist_sq)
#  return g
#
#def add_bias(tensor, init=None, name=None):
#  """Add a bias term to a tensor.
#
#  Parameters
#  ---------- 
#  tensor: tf.Tensor
#    Variable tensor.
#  init: float
#    Bias initializer. Defaults to zero.
#  name: str
#    Name for this op. Defaults to tensor.op.name.
#
#  Returns
#  -------
#  tf.Tensor
#    A biased tensor with the same shape as the input tensor.
#  """
#  if init is None:
#    init = tf.zeros([tensor.get_shape()[-1].value])
#  with tf.name_scope(name, tensor.op.name, [tensor]):
#    b = tf.Variable(init, name='b')
#    return tf.nn.bias_add(tensor, b)
#
#
#def dropout(tensor, dropout_prob, training=True, training_only=True):
#  """Random dropout.
#
#  This implementation supports "always-on" dropout (training_only=False), which
#  can be used to calculate model uncertainty. See Gal and Ghahramani,
#  http://arxiv.org/abs/1506.02142.
#
#  NOTE(user): To simplify the implementation, I have chosen not to reverse
#    the scaling that occurs in tf.nn.dropout when using dropout during
#    inference. This shouldn't be an issue since the activations will be scaled
#    by the same constant in both training and inference. This means that there
#    are no training-time differences between networks that use dropout during
#    inference and those that do not.
#
#  Parameters
#  ---------- 
#  tensor: tf.Tensor
#    Input tensor.
#  dropout_prob: float
#    Float giving dropout probability for weights (NOT keep probability).
#  training_only: bool
#    Boolean. If True (standard dropout), apply dropout only
#    during training. If False, apply dropout during inference as well.
#
#  Returns
#  -------
#  tf.Tensor:
#    A tensor with the same shape as the input tensor.
#  """
#  if not dropout_prob:
#    return tensor  # do nothing
#  keep_prob = 1.0 - dropout_prob
#  if training or not training_only:
#    tensor = tf.nn.dropout(tensor, keep_prob)
#  return tensor
#
#
#def fully_connected_layer(tensor, size=None, weight_init=None, bias_init=None,
#                          name=None):
#  """Fully connected layer.
#
#  Parameters
#  ----------
#  tensor: tf.Tensor
#    Input tensor.
#  size: int
#    Number of output nodes for this layer.
#  weight_init: float
#    Weight initializer.
#  bias_init: float
#    Bias initializer.
#  name: str
#    Name for this op. Defaults to 'fully_connected'.
#
#  Returns
#  -------
#  tf.Tensor:
#    A new tensor representing the output of the fully connected layer.
#
#  Raises
#  ------
#  ValueError
#    If input tensor is not 2D.
#  """
#  if len(tensor.get_shape()) != 2:
#    raise ValueError('Dense layer input must be 2D, not %dD'
#                     % len(tensor.get_shape()))
#  if weight_init is None:
#    num_features = tensor.get_shape()[-1].value
#    weight_init = tf.truncated_normal([num_features, size], stddev=0.01)
#  if bias_init is None:
#    bias_init = tf.zeros([size])
#
#  with tf.name_scope(name, 'fully_connected', [tensor]):
#    w = tf.Variable(weight_init, name='w', dtype=tf.float32)
#    b = tf.Variable(bias_init, name='b', dtype=tf.float32)
#    return tf.nn.xw_plus_b(tensor, w, b)
#
#def weight_decay(penalty_type, penalty):
#  """Add weight decay.
#
#  Args:
#    model: TensorflowGraph.
#
#  Returns:
#    A scalar tensor containing the weight decay cost.
#
#  Raises:
#    NotImplementedError: If an unsupported penalty type is requested.
#  """
#  variables = []
#  # exclude bias variables
#  for v in tf.trainable_variables():
#    if v.get_shape().ndims == 2:
#      variables.append(v)
#
#  with tf.name_scope('weight_decay'):
#    if penalty_type == 'l1':
#      cost = tf.add_n([tf.reduce_sum(tf.abs(v)) for v in variables])
#    elif penalty_type == 'l2':
#      cost = tf.add_n([tf.nn.l2_loss(v) for v in variables])
#    else:
#      raise NotImplementedError('Unsupported penalty_type %s' % penalty_type)
#    cost *= penalty
#    tf.scalar_summary('Weight Decay Cost', cost)
#  return cost
#
#
#def multitask_logits(features, num_tasks, num_classes=2, weight_init=None,
#                     bias_init=None, dropout_prob=None, name=None):
#  """Create a logit tensor for each classification task.
#
#  Args:
#    features: A 2D tensor with dimensions batch_size x num_features.
#    num_tasks: Number of classification tasks.
#    num_classes: Number of classes for each task.
#    weight_init: Weight initializer.
#    bias_init: Bias initializer.
#    dropout_prob: Float giving dropout probability for weights (NOT keep
#      probability).
#    name: Name for this op. Defaults to 'multitask_logits'.
#
#  Returns:
#    A list of logit tensors; one for each classification task.
#  """
#  logits_list = []
#  with tf.name_scope('multitask_logits'):
#    for task_idx in range(num_tasks):
#      with tf.name_scope(name,
#                       ('task' + str(task_idx).zfill(len(str(num_tasks)))), [features]):
#        logits_list.append(
#            logits(features, num_classes, weight_init=weight_init,
#                   bias_init=bias_init, dropout_prob=dropout_prob))
#  return logits_list
#
#
#def logits(features, num_classes=2, weight_init=None, bias_init=None,
#           dropout_prob=None, name=None):
#  """Create a logits tensor for a single classification task.
#
#  You almost certainly don't want dropout on there -- it's like randomly setting
#  the (unscaled) probability of a target class to 0.5.
#
#  Args:
#    features: A 2D tensor with dimensions batch_size x num_features.
#    num_classes: Number of classes for each task.
#    weight_init: Weight initializer.
#    bias_init: Bias initializer.
#    dropout_prob: Float giving dropout probability for weights (NOT keep
#      probability).
#    name: Name for this op.
#
#  Returns:
#    A logits tensor with shape batch_size x num_classes.
#  """
#  with tf.name_scope(name, 'logits', [features]) as name:
#    return dropout(
#        fully_connected_layer(features, num_classes, weight_init=weight_init,
#                              bias_init=bias_init, name=name),
#        dropout_prob)
#
#
#def softmax_N(tensor, name=None):
#  """Apply softmax across last dimension of a tensor.
#
#  Args:
#    tensor: Input tensor.
#    name: Name for this op. If None, defaults to 'softmax_N'.
#
#  Returns:
#    A tensor with softmax-normalized values on the last dimension.
#  """
#  with tf.name_scope(name, 'softmax_N', [tensor]):
#    exp_tensor = tf.exp(tensor)
#    reduction_indices = [tensor.get_shape().ndims - 1]
#    return tf.div(exp_tensor,
#                  tf.reduce_sum(exp_tensor,
#                                reduction_indices=reduction_indices,
#                                keep_dims=True))
#
#def optimizer(optimizer="adam", learning_rate=.001, momentum=.9):
#  """Create model optimizer.
#
#  Parameters
#  ----------
#  optimizer: str, optional
#    Name of optimizer
#  learning_rate: float, optional
#    Learning rate for algorithm
#  momentum: float, optional
#    Momentum rate
#
#  Returns
#  -------
#    A training Optimizer.
#
#  Raises:
#    NotImplementedError: If an unsupported optimizer is requested.
#  """
#  # TODO(user): gradient clipping (see Minimize)
#  if optimizer == 'adagrad':
#    train_op = tf.train.AdagradOptimizer(learning_rate)
#  elif optimizer == 'adam':
#    train_op = tf.train.AdamOptimizer(learning_rate)
#  elif optimizer == 'momentum':
#    train_op = tf.train.MomentumOptimizer(learning_rate,
#                                          momentum)
#  elif optimizer == 'rmsprop':
#    train_op = tf.train.RMSPropOptimizer(learning_rate,
#                                         momentum)
#  elif optimizer == 'sgd':
#    train_op = tf.train.GradientDescentOptimizer(learning_rate)
#  else:
#    raise NotImplementedError('Unsupported optimizer %s' % optimizer)
#  return train_op
