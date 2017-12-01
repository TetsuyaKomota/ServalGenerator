# coding = utf-8
# 2018 年のあれ

from keras import backend as K
from keras.models import Sequential
from keras.layers import Dense, Reshape
from keras.layers.core import Lambda
from keras.layers.convolutional import UpSampling2D
from keras.layers import Conv2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.pooling import AveragePooling2D
from keras.optimizers import Adam

import numpy as np

import models.FriendsLoader as FriendsLoader
from setting import D_LR
from setting import D_BETA
from setting import G_LR
from setting import G_BETA
# G, D それぞれ，次の3層を追加するメソッド
# G の pixel-wise 正規化の正規化関数
# train
#   αの扱い
#   3層挿入のタイミング

# 3層追加メソッド
# filters : 入力の filter 数
def getAdditionalBlock_G(filters):
    model = Sequential()
    layerSize = int(2048/filters)
    model.add(UpSampling2D((2, 2), input_shape=(layerSize, layerSize, filters)))
    model.add(Conv2D(int(filters/2), (3, 3), padding="same"))
    model.add(Lambda(lambda x:x/np.sum(x**2+1e-8, axis=0)))
    model.add(LeakyReLU(0.2))
    model.add(Conv2D(int(filters/2), (3, 3), padding="same"))
    model.add(Lambda(lambda x:x/np.sum(x**2+1e-8, axis=0)))
    model.add(LeakyReLU(0.2))
    return model

# filters : 出力の filter 数
def getAdditionalBlock_D(filters):
    model = Sequential()
    layerSize = int((2048/filters) * 2)
    model.add(Conv2D(int(filters/2), (3, 3), padding="same", input_shape=(layerSize, layerSize, int(filters/2))))
    model.add(LeakyReLU(0.2))
    model.add(Conv2D(int(filters),   (3, 3), padding="same"))
    model.add(LeakyReLU(0.2))
    model.add(AveragePooling2D((2, 2)))
    return model

# D の入力層を生成
def getInputBlock_D(filters):
    model = Sequential()
    model.add(Conv2D(int(filters), (1, 1), padding="same", input_shape=(128, 128, 3)))
    model.add(LeakyReLU(0.2))
    return model

# 最初のモデルを生成
def firstModel_G():
    model = Sequential()
    model.add(Dense(4*4*512, input_shape=(512, )))
    model.add(Reshape((4, 4, 512)))
    model.add(Conv2D(512, (4, 4), padding="same"))
    model.add(Lambda(lambda x:x/np.sum(x**2+1e-8, axis=0)))
    model.add(LeakyReLU(0.2))
    model.add(Conv2D(512, (3, 3), padding="same"))
    model.add(Lambda(lambda x:x/np.sum(x**2+1e-8, axis=0)))
    model.add(LeakyReLU(0.2))
    return model

def firstModel_D():
    model = Sequential()
    model.add(Lambda(lambda x:K.concatenate([K.std(x, axis=0, keepdims=True), x], axis=0), input_shape=(4, 4, 512)))
    model.add(Conv2D(512, (3, 3), padding="same"))
    model.add(LeakyReLU(0.2))
    model.add(Conv2D(512, (4, 4), padding="same"))
    model.add(LeakyReLU(0.2))
    model.add(Dense(1))
    return model

# 学習
def train():
    (datas, _), (_, _) = FriendsLoader.load_data()
    datas = (datas.astype(np.float32) - 127.5)/127.5
    shape = datas.shape
    datas = datas.reshape(shape[0], shape[1], shape[2], 3)

    g_opt          = Adam(lr=G_LR, beta_1=G_BETA)
    d_opt          = Adam(lr=D_LR, beta_1=D_BETA)

    # 各モデルをロード
    # メモリ的に 128*128 を最終目標
    # つまり 本体 + 5 ブロック (4 * 2**5 = 128)
    models_G = []
    models_D = []
    models_G.append(firstModel_G())
    models_D.append(firstModel_D())
    for i in range(5):
        models_G.append(getAdditionalBlock_G(512/(2**i)))
        models_D.append(getAdditionalBlock_D(512/(2**i)))

    # 各段階で入出力層を補ってコンパイル
    """
    gan = Sequential([models_G[0], models_D[0]])
    gan.compile(loss="binary_crossentropy", \
                        optimizer=g_opt, metrics=["accuracy"])
    models_D[0].compile(loss="binary_crossentropy", \
                        optimizer=d_opt, metrics=["accuracy"])
    compiled_G = [gan]
    compiled_D = [models_D[0]]
    """
  
    compiled_G = []
    compiled_D = []
    for i in range(5+1):
        print(i)
        # G の出力層
        out_G = Sequential([Conv2D(3, (1, 1), padding="same", input_shape=(int(512/(2**i)), int(512/(2**i)), 4*2**i))])
        # D の入力層
        in_D  = getInputBlock_D(512/(2**(i)))
        print(type(models_G))
        print(models_G)
        print(models_G[:i+1] + [out_G, in_D] + models_D[:i+1][::-1])
        compiled_D.append(Sequential([in_D] + models_D[:i+1][::-1]))
        compiled_G.append(Sequential(models_G[:i+1] + [out_G, in_D] + models_D[:i+1][::-1]))
    #     compiled_G.append(Sequential([out_G, in_D] + models_D[:i+1][::-1]))

        compiled_G[-1].compile(loss="binary_crossentropy", \
                        optimizer=g_opt, metrics=["accuracy"])
        compiled_G[-1].summary()

        print(type([in_D] + models_D[:i+1][::-1]))
        print([in_D] + models_D[:i+1][::-1])
        compiled_D[-1].compile(loss="binary_crossentropy", \
                        optimizer=d_opt, metrics=["accuracy"])
        compiled_D[-1].summary()

    # モデルを表示










