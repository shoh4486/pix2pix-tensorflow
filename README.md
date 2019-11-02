# pix2pix-TensorFlow
- Official paper: Isola, P. et al., Image-to-image translation with conditional adversarial networks, arXiv:1611.07004.
- Paper link: http://openaccess.thecvf.com/content_cvpr_2017/html/Isola_Image-To-Image_Translation_With_CVPR_2017_paper.html
- A powerful deep learning architecture for image-to-image translation
- CNN-based encoder-decoder with a conditional GAN architecture
- Image size < 400 x 400 recommended (Higher resolution image -> Use pix2pixHD)
## In this code
- Latent variable z was removed for deterministic mapping (i.e. input image and ground truth image are 1:1 matched)
- tf.\_\_version\_\_ == '1.12.0' ~ '1.14.0'
- Only CPU: set FLAGS.gpu_num to 0 in main.py.
- The number of GPUs > 2: mannually allocate them.
## Author
Sehyeok Oh  @shoh4486
## Author's application
- Prediction of hardness distribution in laser transformation hardening (R2 accuracy: 94.4%).
