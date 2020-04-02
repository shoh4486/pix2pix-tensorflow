# pix2pix-TensorFlow
- Official paper: Isola, P. et al., Image-to-image translation with conditional adversarial networks, arXiv:1611.07004.
- Paper link: http://openaccess.thecvf.com/content_cvpr_2017/html/Isola_Image-To-Image_Translation_With_CVPR_2017_paper.html
- A powerful deep learning architecture for image-to-image translation
- CNN-based encoder-decoder with a conditional GAN architecture
- Image size < 400 x 400 recommended (Higher resolution image: Use pix2pixHD)
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
- **Deep learning model for predicting hardness distribution in laser heat treatment of AISI H13 tool steel, *Applied Thermal Engineering* 153, 583-595 (2019)**
- Inputs: FEM-simulated cross-sectional temperature profile, Outputs: Cross-sectional hardness distribution
- GAN generation tracking (No validation set, as the validation was carried out by cross-validation; epoch: 0~460)
  - **Training set (Process conditions: 'c', 'f', 'h' with their ground truths; from left-to-right, top-to-bottom)**
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78258584-69af4780-7536-11ea-9ad5-9a08de8706a8.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243516-dae30080-751e-11ea-8d86-e352471e565c.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78258588-6ae07480-7536-11ea-8f6d-c744583f66af.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243609-06fe8180-751f-11ea-943f-345d5c2a6ba2.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78258590-6b790b00-7536-11ea-95b6-affbb82b8d09.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243682-27c6d700-751f-11ea-8beb-abd0aa59d68d.png>
  
  - **Test set (Process conditions: 'a', 'b', 'd', 'e', 'f' with their ground truths; from left-to-right, top-to-bottom)**
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78258591-6c11a180-7536-11ea-939e-917552ed6912.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78244107-ef73c880-751f-11ea-8e54-48d6c5715680.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78258577-67e58400-7536-11ea-9215-328988c5a51a.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243905-96a43000-751f-11ea-8983-2b829834b69e.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78258586-6a47de00-7536-11ea-819a-7e265bb8463c.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243933-a459b580-751f-11ea-96eb-d74f261d938d.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78258587-6a47de00-7536-11ea-8388-337718409a74.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243966-b20f3b00-751f-11ea-86bb-07e7e838237b.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78258589-6b790b00-7536-11ea-8476-50f35a4ce05a.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78244013-c2bfb100-751f-11ea-8025-c83df4acbc74.png>
  
- **Result at the validated epoch (R2 accuracy: 94.4%)** 
  <img width='700' src="https://user-images.githubusercontent.com/39050306/68071460-edb1a780-fdbd-11e9-9e79-f83ab867e11f.png">
