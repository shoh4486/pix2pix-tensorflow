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
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78240851-8178d280-751a-11ea-9aa2-b619d7dfb1f2.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243516-dae30080-751e-11ea-8d86-e352471e565c.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78240473-06172100-751a-11ea-96b3-bdd337893a39.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243609-06fe8180-751f-11ea-943f-345d5c2a6ba2.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78241031-bedd6000-751a-11ea-87ae-e913ddad73b4.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243682-27c6d700-751f-11ea-8beb-abd0aa59d68d.png>
  
  - **Test set (Process conditions: 'a', 'b', 'd', 'e', 'f' with their ground truth; from left-to-right, top-to-bottom)**
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78244102-edaa0500-751f-11ea-9c7c-566a05b95332.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78244107-ef73c880-751f-11ea-8e54-48d6c5715680.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243899-94da6c80-751f-11ea-859e-f2ab6c416442.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243905-96a43000-751f-11ea-8983-2b829834b69e.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243930-a28ff200-751f-11ea-9269-4a23400bc245.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243933-a459b580-751f-11ea-96eb-d74f261d938d.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243958-aface100-751f-11ea-9a83-0c21eeca6f5b.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78243966-b20f3b00-751f-11ea-86bb-07e7e838237b.png>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78244007-c0f5ed80-751f-11ea-8b9c-d5f0981f939d.gif>
  <img width='200' src=https://user-images.githubusercontent.com/39050306/78244013-c2bfb100-751f-11ea-8025-c83df4acbc74.png>
  
- **Result at the validated epoch (R2 accuracy: 94.4%)**
  <img width='700' src="https://user-images.githubusercontent.com/39050306/68071460-edb1a780-fdbd-11e9-9e79-f83ab867e11f.png">
