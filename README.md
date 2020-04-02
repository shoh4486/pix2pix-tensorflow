# pix2pix-TensorFlow
- Official paper: Isola, P. et al., Image-to-image translation with conditional adversarial networks, arXiv:1611.07004.
- Paper link: http://openaccess.thecvf.com/content_cvpr_2017/html/Isola_Image-To-Image_Translation_With_CVPR_2017_paper.html
- A powerful deep learning architecture for image-to-image translation
- CNN-based encoder-decoder with a conditional GAN architecture
- Image size < 400 x 400 recommended (Higher resolution image -> Use pix2pixHD)
## In this code
- Latent variable z was removed for deterministic mapping (i.e. input image and ground truth image are 1:1 matched).
- tf.\_\_version\_\_ == '1.12.0' ~ '1.15.0'
- The number of GPUs > 2: mannually allocate them.
- **Inputs shape: (N, H, W, C_in) (-1~1)**       
- **Ground truths shape: (N, H, W, C_out) (-1~1)**
- Normalization from min\~max to -1\~1: (data - 0.5*(max + min))/(0.5*(max - min))
## Run example
- training mode:
```
$ python main.py --trial_num=1 --height=100 --width=100 --train=True --start_epoch=0 --end_epoch=200 --gpu_alloc=1,2
```
- testing mode: 
```
$ python main.py --trial_num=2 --train=False --restore=True --restore_trial_num=1 --restore_sess_num=199 --eval_with_test_acc=True --gpu_alloc=1,2
```
- Add other FLAGS options if necessary
## Author
Sehyeok Oh  @shoh4486
## Author's application
- Deep learning model for predicting hardness distribution in laser heat treatment of AISI H13 tool steel, *Applied Thermal Engineering* 153, 583-595 (2019).
- Inputs: FEM-simulated cross-sectional temperature profile, Outputs: Cross-sectional hardness distribution
- Training tracking (No validation set, as the validation was carried out by cross-validation; epoch: 0~460)
  - **Training set (Process conditions: 'c', 'f', 'h' with their ground truth; from left-to-right, top-to-bottom)**
  
  
- **Result at the validated epoch (R2 accuracy: 94.4%)**
  <img width='700' src="https://user-images.githubusercontent.com/39050306/68071460-edb1a780-fdbd-11e9-9e79-f83ab867e11f.png">
