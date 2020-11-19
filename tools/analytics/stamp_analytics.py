#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2018 Slightech Co., Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=missing-docstring
from __future__ import print_function

import os
import sys

TOOLBOX_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(TOOLBOX_DIR, 'internal'))

# pylint: disable=import-error,wrong-import-position
from data import ROSBag, MYNTEYE, What

ANGLE_DEGREES = 'd'
ANGLE_RADIANS = 'r'
ANGLE_UNITS = (ANGLE_DEGREES, ANGLE_RADIANS)

BIN_IMG_NAME = 'stamp_analytics_img.bin'
BIN_IMU_NAME = 'stamp_analytics_imu.bin'

RESULT_FIGURE = 'stamp_analytics.png'


IMU_ALL = 0
IMU_ACCEL = 1
IMU_GYRO = 2


class BinDataset(object):

  def __init__(self, path, dataset_creator):
    self.path = path
    self.dataset_creator = dataset_creator
    self._digest()

  def _digest(self):
    bindir = os.path.splitext(self.path)[0]
    binimg = os.path.join(bindir, BIN_IMG_NAME)
    binimu = os.path.join(bindir, BIN_IMU_NAME)
    if os.path.isfile(binimg) and os.path.isfile(binimu):
      print('find binary files ...')
      print('  binimg: {}'.format(binimg))
      print('  binimu: {}'.format(binimu))
      while True:
        sys.stdout.write('Do you want to use it directly? [Y/n] ')
        choice = raw_input().lower()
        if choice == '' or choice == 'y':
          self._binimg = binimg
          self._binimu = binimu
          self._has_img = True
          self._has_imu = True
          return
        elif choice == 'n':
          break
        else:
          print('Please respond with \'y\' or \'n\'.')
    self._convert()

  def _convert(self):
    import numpy as np

    dataset = self.dataset_creator(self.path)
    bindir = os.path.splitext(self.path)[0]
    if not os.path.exists(bindir):
      os.makedirs(bindir)
    binimg = os.path.join(bindir, BIN_IMG_NAME)
    binimu = os.path.join(bindir, BIN_IMU_NAME)
    print('save to binary files ...')
    print('  binimg: {}'.format(binimg))
    print('  binimu: {}'.format(binimu))

    has_img = False
    has_imu = False
    with open(binimg, 'wb') as f_img, open(binimu, 'wb') as f_imu:
      img_count = 0
      imu_count = 0
      for result in dataset.generate(What.img_left, What.imu):
        if What.img_left in result:
          img = result[What.img_left]
          np.array([(
              img.timestamp
          )], dtype="f8").tofile(f_img)
          img_count = img_count + 1
          has_img = True
        if What.imu in result:
          imu = result[What.imu]
          np.array([(
              imu.timestamp, imu.flag,
              imu.accel_x, imu.accel_y, imu.accel_z,
              imu.gyro_x, imu.gyro_y, imu.gyro_z
          )], dtype="f8, i4, f8, f8, f8, f8, f8, f8").tofile(f_imu)
          imu_count = imu_count + 1
          has_imu = True
        sys.stdout.write('\r  img: {}, imu: {}'.format(img_count, imu_count))
      sys.stdout.write('\n')

    # pylint: disable=attribute-defined-outside-init
    self._binimg = binimg
    self._binimu = binimu
    self._has_img = has_img
    self._has_imu = has_imu

  def stamp_analytics(self, args):
    import numpy as np
    if self.has_img:
      # pd.cut fails on readonly arrays
      #   https://github.com/pandas-dev/pandas/issues/18773
      # imgs = np.memmap(self._binimg, dtype=[
      #     ('t', 'f8')
      # ], mode='r')
      imgs = np.fromfile(self._binimg, dtype=[
          ('t', 'f8')
      ])
    else:
      sys.exit("Error: there are no imgs.")

    if self.has_imu:
      imus = np.memmap(self._binimu, dtype=[
          ('t', 'f8'), ('flag', 'i4'),
          ('accel_x', 'f8'), ('accel_y', 'f8'), ('accel_z', 'f8'),
          ('gyro_x', 'f8'), ('gyro_y', 'f8'), ('gyro_z', 'f8'),
      ], mode='r')
    else:
      sys.exit("Error: there are no imus.")

    period_img = 1. / args.rate_img
    period_imu = 1. / args.rate_imu
    print('\nrate (Hz)')
    print('  img: {}, imu: {}'.format(args.rate_img, args.rate_imu))
    print('sample period (s)')
    print('  img: {}, imu: {}'.format(period_img, period_imu))

    imgs_t_diff = np.diff(imgs['t'])
    # imus_t_diff = np.diff(imus['t'])

    accel = imus[(imus['flag'] == IMU_ALL) | (imus['flag'] == IMU_ACCEL)]
    accel_t_diff = np.diff(accel['t'])
    gyro = imus[(imus['flag'] == IMU_ALL) | (imus['flag'] == IMU_GYRO)]
    gyro_t_diff = np.diff(gyro['t'])

    print('\ncount')
    print('  imgs: {}, imus: {}, accel: {}, gyro: {}'.format(
        imgs.size, imus.size, accel.size, gyro.size))
    print('\ndiff count')
    print('  imgs_t_diff: {}, accel_t_diff: {}, gyro_t_diff: {}'.format(
        imgs_t_diff.size, accel_t_diff.size, gyro_t_diff.size))

    print('\ndiff where (factor={})'.format(args.factor))
    self._print_t_diff_where('imgs', imgs_t_diff, period_img, args.factor)
    # self._print_t_diff_where('imus', imus_t_diff, period_imu, args.factor)
    self._print_t_diff_where('accel', accel_t_diff, period_imu, args.factor)
    self._print_t_diff_where('gyro', gyro_t_diff, period_imu, args.factor)

    import pandas as pd
    bins = imgs['t']
    bins_n = imgs['t'].size
    bins = pd.Series(data=bins).drop_duplicates(keep='first')

    print('\nimage timestamp duplicates: {}'.format(bins_n - bins.size))

    def _cut_by_imgs_t(imus_t):
      cats = pd.cut(imus_t, bins)
      return cats.value_counts()

    self._plot(args.outdir, args.show_secs, imgs_t_diff,
        accel_t_diff, _cut_by_imgs_t(accel['t']),
        gyro_t_diff, _cut_by_imgs_t(gyro['t']))

  def _print_t_diff_where(self, name, t_diff, period, factor):
    import numpy as np

    where = np.argwhere(t_diff > period * (1 + factor))
    print('  {} where diff > {}*{} ({})'.format(
        name, period, 1 + factor, where.size))
    for x in where:
      print('  {:8d}: {:.16f}'.format(x[0], t_diff[x][0]))

    where = np.argwhere(t_diff < period * (1 - factor))
    print('  {} where diff < {}*{} ({})'.format(
        name, period, 1 - factor, where.size))
    for x in where:
      print('  {:8d}: {:.16f}'.format(x[0], t_diff[x][0]))

  def _plot(self, outdir, show_secs, imgs_t_diff,
            accel_t_diff, accel_counts, gyro_t_diff, gyro_counts):
    import matplotlib.pyplot as plt
    import numpy as np

    fig_1 = plt.figure(1, [16, 12])
    fig_1.suptitle('Stamp Analytics')
    fig_1.subplots_adjust(
        left=0.1,
        right=0.95,
        top=0.85,
        bottom=0.15,
        wspace=0.4,
        hspace=0.4)

    ax_imgs_t_diff = fig_1.add_subplot(231)
    ax_imgs_t_diff.set_title('Image Timestamp Diff')
    ax_imgs_t_diff.set_xlabel('diff index')
    ax_imgs_t_diff.set_ylabel('diff (s)')
    ax_imgs_t_diff.axis('auto')

    ax_imgs_t_diff.set_xlim([0, imgs_t_diff.size])
    ax_imgs_t_diff.plot(imgs_t_diff)

    def _plot_imus(name, t_diff, counts, pos_offset=0):
      ax_imus_t_diff = fig_1.add_subplot(232 + pos_offset)
      ax_imus_t_diff.set_title('{} Timestamp Diff'.format(name))
      ax_imus_t_diff.set_xlabel('diff index')
      ax_imus_t_diff.set_ylabel('diff (s)')
      ax_imus_t_diff.axis('auto')

      ax_imus_t_diff.set_xlim([0, t_diff.size - 1])
      ax_imus_t_diff.plot(t_diff)

      ax_imus_counts = fig_1.add_subplot(233 + pos_offset)
      ax_imus_counts.set_title('{} Count Per Image Intervel'.format(name))
      ax_imus_counts.set_xlabel('intervel index')
      ax_imus_counts.set_ylabel('imu count')
      ax_imus_counts.axis('auto')

      # print(counts.values)
      # counts.plot(kind='line', ax=ax_imus_counts)
      data = counts.values
      ax_imus_counts.set_xlim([0, data.size])
      ax_imus_counts.set_ylim([np.min(data) - 1, np.max(data) + 1])
      ax_imus_counts.plot(data)

    _plot_imus('Accel', accel_t_diff, accel_counts)
    _plot_imus('Gyro', gyro_t_diff, gyro_counts, 3)

    if outdir:
      figpath = os.path.join(outdir, RESULT_FIGURE)
      print('\nsave figure to:\n  {}'.format(figpath))
      if not os.path.exists(outdir):
        os.makedirs(outdir)
      fig_1.savefig(figpath, dpi=100)

    if show_secs > 0:
      plt.show(block=False)
      plt.pause(show_secs)
      plt.close()
    else:
      plt.show()

  @property
  def has_img(self):
    return self._has_img

  @property
  def has_imu(self):
    return self._has_imu


def _parse_args():
  import argparse
  parser = argparse.ArgumentParser(
      prog=os.path.basename(__file__),
      formatter_class=argparse.RawTextHelpFormatter,
      description='usage examples:'
      '\n  python %(prog)s -i DATASET')
  parser.add_argument(
      '-i',
      '--input',
      dest='input',
      metavar='DATASET',
      required=True,
      help='the input dataset path')
  parser.add_argument(
      '-o',
      '--outdir',
      dest='outdir',
      metavar='OUTDIR',
      help='the output directory')
  parser.add_argument(
      '-c',
      '--config',
      dest='config',
      metavar='CONFIG',
      help='yaml config file about input dataset')
  parser.add_argument(
      '-f',
      '--factor',
      dest='factor',
      metavar='FACTOR',
      default=0.1,
      type=float,
      help='the wave factor (default: %(default)s)')
  parser.add_argument(
      '--rate-img',
      dest='rate_img',
      metavar='RATE',
      default=30,
      type=int,
      help='the img rate (default: %(default)s)')
  parser.add_argument(
      '--rate-imu',
      dest='rate_imu',
      metavar='RATE',
      default=200,
      type=int,
      help='the imu rate (default: %(default)s)')
  parser.add_argument(
      '--show-secs',
      dest='show_secs',
      metavar='SECONDS',
      default=0,
      type=int,
      help='the show seconds (default: %(default)s)')
  return parser.parse_args()


def _main():
  args = _parse_args()

  dataset_path = args.input
  if not dataset_path or not os.path.exists(dataset_path):
    sys.exit('Error: the dataset path not exists, %s' % dataset_path)
  dataset_path = os.path.normpath(dataset_path)

  outdir = args.outdir
  if not args.outdir:
    outdir = os.path.splitext(dataset_path)[0]
  else:
    outdir = os.path.abspath(outdir)
  args.outdir = outdir

  print('stamp analytics ...')
  print('  input: %s' % dataset_path)
  print('  outdir: %s' % outdir)

  def dataset_creator(path):
    print('open dataset ...')
    if args.config:
      import yaml
      config = yaml.load(file(args.config, 'r'))
      model = config['dataset']
      if model == 'rosbag':
        dataset = ROSBag(path, **config['rosbag'])
      elif model == 'mynteye':
        dataset = MYNTEYE(path)
      else:
        sys.exit('Error: dataset model not supported {}'.format(model))
    else:
      dataset = ROSBag(path,
                       topic_img_left='/mynteye/left/image_color',
                       topic_imu='/mynteye/imu/data_raw')
    return dataset

  dataset = BinDataset(dataset_path, dataset_creator)
  dataset.stamp_analytics(args)

  print('stamp analytics done')


if __name__ == '__main__':
  _main()
