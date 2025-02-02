import tensorflow as tf
import numpy as np
import WIFI_ADG_model as atn
import os
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import scipy.io as sio  
from sklearn import preprocessing
import gc
import h5py
import xlwt

#data = sio.loadmat('minmax.mat') # 读取mat文件
# print(data.keys())  # 查看mat文件中的所有变量

#min_ = data['min_'] 
#max_ = data['max_']

book = xlwt.Workbook(encoding='utf-8',style_compression=0)
#sheet = book.add_sheet('mysheet5_9_b',cell_overwrite_ok=True)

FLAGS = tf.flags.FLAGS

tf.flags.DEFINE_boolean('train',0, 'Train and save the ATN model.')

# Placeholder nodes.
images_holder = tf.placeholder(tf.float32, [None, 20,90,1])
label_holder_1 = tf.placeholder(tf.float32, [None, 7])#activity
label_holder_2 = tf.placeholder(tf.float32, [None, 10])#person
label_holder_3 = tf.placeholder(tf.float32, [None, 6])#location

p_keep_holder = tf.placeholder(tf.float32)
rerank_holder = tf.placeholder(tf.float32, [None, 7])

"""
导入数据
"""
data_path = './test data set/data5.mat'
data = h5py.File(data_path)
min_max_scaler = preprocessing.MinMaxScaler(feature_range=(0,1))# default range: (0,1), can be changed.
#train_x = np.transpose(data['train_x'][:])
test_x =np.transpose(data['test_x'][:])

#target_1_train_y = np.transpose(data['train_act'][:])
target_1_test_y = np.transpose(data['test_act'][:])
#target_2_train_y = np.transpose(data['train_per'][:])
target_2_test_y = np.transpose(data['test_per'][:])
#target_3_train_y = np.transpose(data['train_loc'][:])
target_3_test_y = np.transpose(data['test_loc'][:])


def MinMax(train_x, test_x):
    
    train_x = train_x.reshape(-1, 20*90)
    train_x_max = np.max(train_x, axis=0)
    train_x_min = np.min(train_x, axis=0)
    norm_train_x = (train_x-train_x_min)/(train_x_max-train_x_min)
    
    test_x = test_x.reshape(-1, 20*90) 
#    test_x_max = np.max(test_x, axis=0)
#    test_x_min = np.min(test_x, axis=0)
    norm_test_x = (test_x-train_x_min)/(train_x_max-train_x_min)
    
    return norm_train_x, norm_test_x,train_x_max,train_x_min

norm_train_x,norm_test_x, max_, min_ = MinMax(train_x,test_x)   #nomalization

norm_train_x = np.reshape(norm_train_x,[-1,20,90,1])
norm_test_x = np.reshape(norm_test_x,[-1,20,90,1])
#train_x = train_x.reshape(-1, 45*48)
#x_max = np.max(train_x, axis=0)
#x_min = np.min(train_x, axis=0)
#norm_train_x = (train_x-x_min)/(x_max-x_min)
#min_max_scaler = preprocessing.MinMaxScaler(feature_range=(0,1))# default range: (0,1), can be changed.
#norm_train_x = min_max_scaler.fit_transform(train_x) #nomalization



#test_x = test_x.reshape(-1, 20*90)
#norm_test_x = min_max_scaler.transform(test_x)  #nomalization

#test_x = test_x.reshape(-1, 20*90)
#test_x_max = np.max(test_x, axis=0)
#test_x_min = np.min(test_x, axis=0)
#norm_test_x = (test_x-min_)/(max_-min_)
#norm_test_x = np.reshape(norm_test_x,[-1,20,90,1])

del data
gc.collect()#回收data内存


def reverse_norm(norm_x, x_max, x_min):
    
    x = norm_x*(x_max-x_min)+x_min 
    x = x.reshape(-1, 20, 90)
    return x

    

def get_batch(faces,model_1_label,model_2_label,model_3_label,idx):
    batch_xs = faces[idx]
    model_1_batch_ys = model_1_label[idx]
    model_2_batch_ys = model_2_label[idx]
    model_3_batch_ys = model_3_label[idx]
    
    return batch_xs, model_1_batch_ys, model_2_batch_ys, model_3_batch_ys #  generating a batch


def main(arvg=None):
    """
    """
    if FLAGS.train:
        train()
    else:
        test()


def test():
    """
    """
    print("ok\n")
#    batch_size = test_x.shape[0]
    batch_size = 3800
    batch_xs, target_1_batch_ys, target_2_batch_ys, target_3_batch_ys = get_batch(norm_test_x,
                            target_1_test_y, target_2_test_y, target_3_test_y,np.arange(batch_size)) #input several images
    #batch_xs, batch_ys = mnist.test.next_batch(batch_size)
    model = atn.ATN(images_holder, label_holder_1, label_holder_2,label_holder_3, p_keep_holder, rerank_holder)#define ADG model
	
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
#        AE_path = 'AE_for_ATN'
#        AE_path = 'AE_for_loc-act'
        AE_path = 'C_room'
#        AE_path = 'AE_for_per-act_newloss1'
        model.load_ae(sess, './TABLE II/8-layer ADG/classifier5/'+AE_path) # load the model
        model.load_model(sess, './TABLE I/classifier_5') # load ADG model
			
        adv_images = sess.run( 
            model.prediction,
            feed_dict={images_holder: batch_xs} #input the original samples, and output the adversarial ones.
        )    
        
        a = sess.run(model._target1.prediction, feed_dict={
              images_holder: adv_images,
              label_holder_1: target_1_batch_ys,
              p_keep_holder: 1.0
          })
        
        b = sess.run(model._target2.prediction, feed_dict={
              images_holder: adv_images,
              label_holder_2: target_2_batch_ys,
              p_keep_holder: 1.0
          })
    
        c = sess.run(model._target3.prediction, feed_dict={
              images_holder: adv_images,
              label_holder_3: target_3_batch_ys,
              p_keep_holder: 1.0
          })    
    
        print('Attacked model1_accuracy: {0:0.5f}'.format(
            sess.run(model._target1.accuracy, feed_dict={
                images_holder: adv_images,
                #label_holder: mnist.test.labels,
                label_holder_1: target_1_batch_ys,
                p_keep_holder: 1.0
            })))
    
        traget1_pred = sess.run(model._target1.prediction, feed_dict={
                images_holder: batch_xs,
                #label_holder: mnist.test.labels,
                label_holder_1: target_1_batch_ys,
                p_keep_holder: 1.0
            })
        print('Original model1_accuracy: {0:0.5f}'.format(
            sess.run(model._target1.accuracy, feed_dict={
                #images_holder: mnist.test.images,
                #label_holder: mnist.test.labels,
                images_holder: batch_xs,
                label_holder_1:  target_1_batch_ys,
                p_keep_holder: 1
            })))
    
        print('Attacked model2_accuracy: {0:0.5f}'.format(
            sess.run(model._target2.accuracy, feed_dict={
                images_holder: adv_images,
                #label_holder: mnist.test.labels,
                label_holder_2: target_2_batch_ys,
                p_keep_holder: 1.0
            })))
        
        traget2_pred = sess.run(model._target2.prediction, feed_dict={
                images_holder: batch_xs,
                #label_holder: mnist.test.labels,
                label_holder_2: target_2_batch_ys,
                p_keep_holder: 1.0
            })
        print('Original model2_accuracy: {0:0.5f}'.format(
            sess.run(model._target2.accuracy, feed_dict={
                #images_holder: mnist.test.images,
                #label_holder: mnist.test.labels,
                images_holder: batch_xs,
                label_holder_2:  target_2_batch_ys,
                p_keep_holder: 1.0
            })))
        
        print('Attacked model3_accuracy: {0:0.5f}'.format(
            sess.run(model._target3.accuracy, feed_dict={
                images_holder: adv_images,
                #label_holder: mnist.test.labels,
                label_holder_3: target_3_batch_ys,
                p_keep_holder: 1.0
            })))
        
        traget3_pred = sess.run(model._target3.prediction, feed_dict={
                images_holder: batch_xs,
                #label_holder: mnist.test.labels,
                label_holder_3: target_3_batch_ys,
                p_keep_holder: 1.0
            })
        print('Original model3_accuracy: {0:0.5f}'.format(
            sess.run(model._target3.accuracy, feed_dict={
                #images_holder: mnist.test.images,
                #label_holder: mnist.test.labels,
                images_holder: batch_xs,
                label_holder_3:  target_3_batch_ys,
                p_keep_holder: 1.0
            })))
         
        '''temp_adv_y = sess.run(model._target.prediction, feed_dict={
                #images_holder: mnist.test.images,
                #label_holder: mnist.test.labels,
                images_holder: batch_xs,
                label_holder: batch_ys,
                p_keep_holder: 1.0
            })'''
    

        ''' confidence_origin = sess.run(model._target.showY, feed_dict={
        						images_holder: batch_xs,
                				#label_holder: mnist.test.labels,
                				label_holder: batch_ys,
                				p_keep_holder: 1.0
            				})
        					
         confidence_adv = sess.run(model._target.showY, feed_dict={
        						images_holder: adv_images,
                				#label_holder: mnist.test.labels,
                				label_holder: batch_ys,
                				p_keep_holder: 1.0
            				})'''
        show_ori = reverse_norm(batch_xs[0:10],  max_,min_)
        show_adv = reverse_norm(adv_images[0:10], max_,min_)

        # Show some results.
        f, a = plt.subplots(2, 10, figsize=(10, 2))
        for i in range(10):
            a[0][i].imshow(np.reshape(show_ori[i], (20, 90)))
            a[0][i].axis('off')
            a[1][i].axis('off')
            a[1][i].imshow(np.reshape(show_adv[i], (20, 90)))
       
        plt.savefig('./Result/'+AE_path+'.jpg') 
        plt.show()


def train():
    """
    """
    attack_target = 3 #Categories of attacks
    alpha = 1.5 #rerank gives the new probability to y.
    training_epochs = 20000 #Number of training iterations
    batch_size = 128 
    model = atn.ATN(images_holder, label_holder_1, label_holder_2, label_holder_3, p_keep_holder, rerank_holder) #ATN模型
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())

#        AE_path = './Models/AE_for_ATN'
#        AE_path = './Models/AE_for_act+loc-per_newloss'
        AE_path = './classifier_5/C_room'
        print(AE_path)
#   
        model.load_model(sess, './TABLE I/classifier_5') #load the model
        
        total_batch = int(norm_train_x.shape[0]/batch_size)
        batch_idx=np.arange(norm_train_x.shape[0])
        for epoch in range(0,training_epochs):
            batch_offset = 0
            np.random.shuffle(batch_idx)
            for i in range(total_batch):
                batch_xs, target_1_batch_ys, target_2_batch_ys,target_3_batch_ys = get_batch(norm_train_x, target_1_train_y, target_2_train_y, 
                                                                 target_3_train_y,batch_idx[batch_offset:batch_offset+batch_size]) #每次输入若干张图像
                batch_offset = batch_offset+batch_size
            #    r_res = sess.run(model._target1.prediction,   
            #                     feed_dict={
            #                         images_holder: batch_xs,
            #                         p_keep_holder: 1.0
            #                     })
    
            #    target2_prob = sess.run(model._target2.prediction,   
            #                     feed_dict={
            #                         images_holder: batch_xs,
            #                         p_keep_holder: 1.0
            #                     })  
    
            #    r_res[:, attack_target] = np.max(r_res, axis=1) * alpha  #r(y,t)，
                            
             #   norm_div = np.linalg.norm(r_res, axis=1) 
             #   for i in range(len(r_res)):
             #       r_res[i] /= norm_div[i]   # r(y,t) = r(y,t)/norm(r(y,t))，

                _,loss,L0,L1, L2,L3 = sess.run(model.optimization, feed_dict={
                    images_holder: batch_xs,
                    label_holder_1: target_1_batch_ys,
                    label_holder_2: target_2_batch_ys,
                    label_holder_3: target_3_batch_ys,
                    p_keep_holder: 1.,
                    rerank_holder: target_1_batch_ys
                    
                })
            
            print('Eopch {0} completed. loss={1:.3f}.L0={2:.3f},Lx={3:.3f}.Ly={4:.3f},Lz={5:.3f}'.
                  format(epoch+1, loss,L0, L1, L2,L3))
            if epoch%10==0:
#                epoch_num=epoch/10
                epoch_dir = AE_path + '/epoch='+ str(epoch)
                if os.path.exists(epoch_dir) == 0:
                    os.makedirs(epoch_dir)
                model.save_ae(sess, epoch_dir)
#                book.save('./new_models5_9/mysheet5_9.xls')
#            if epoch%1==0:
#                epoch_num=epoch/10
            sheet.write(int(epoch),0,'epoch_num='+str(epoch))
            sheet.write(int(epoch),1,'loss='+str(loss))
            sheet.write(int(epoch),2,'act='+str(L1))
            sheet.write(int(epoch),3,'per='+str(L2))
            sheet.write(int(epoch),4,'loc='+str(L3))
            
#                model.save_ae(sess, epoch_dir)
#            book.save('./new_models5_9new/mysheet5_9_b.xls')

#            model.save_ae(sess, AE_path)
#            print("Trained params have been saved to './Models/AE_for_ATN/AE_CSI'")
        print("Optimization Finished!")
      


if __name__ == '__main__':
    main()
