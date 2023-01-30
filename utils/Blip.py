# -*- coding: utf-8 -*-
# @Time    : 1/30/23 11:01 AM
# @FileName: Blip.py
# @Software: PyCharm
# @Github    ：sudoskys
import os
import torch
import atexit
import inspect
from dataclasses import dataclass
from blip.models.blip import blip_decoder, BLIP_Decoder
from PIL import Image
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode


@dataclass
class Config:
    # models can optionally be passed in directly
    blip_model: BLIP_Decoder = None

    # blip settings
    blip_image_eval_size: int = 384
    blip_max_length: int = 32
    blip_model_url: str = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/models/model_large_caption.pth'
    blip_num_beams: int = 8
    blip_offload: bool = False

    # interrogator settings
    cache_path: str = 'cache'
    chunk_size: int = 2048
    data_path: str = os.path.join(os.path.dirname(__file__), 'data')
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    flavor_intermediate_count: int = 2048
    quiet: bool = False  # when quiet progress bars are not shown
    model: str = 'large'


class Interrogator(object):
    def __init__(self, config: Config):
        self.config = config
        self.device = config.device
        if self.config.model == 'base':
            self.config.blip_model_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/models/model_base_caption_capfilt_large.pth'
        if config.blip_model is None:
            if not config.quiet:
                print("Loading BLIP model...")
            print(f'>>>>>>>> Using model {config.model}')
            blip_path = os.path.dirname(inspect.getfile(blip_decoder))
            configs_path = os.path.join(os.path.dirname(blip_path), 'configs')
            med_config = os.path.join(configs_path, 'med_config.json')
            blip_model = blip_decoder(
                pretrained=config.blip_model_url,
                image_size=config.blip_image_eval_size,
                vit=config.model,
                med_config=med_config
            )
            blip_model.eval()
            blip_model = blip_model.to(config.device)
            self.blip_model = blip_model
        else:
            self.blip_model = config.blip_model

    def generate_caption(self, pil_image: Image) -> str:
        if self.config.blip_offload:
            self.blip_model = self.blip_model.to(self.device)
        size = self.config.blip_image_eval_size
        gpu_image = transforms.Compose([
            transforms.Resize((size, size), interpolation=InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
        ])(pil_image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            caption = self.blip_model.generate(
                gpu_image,
                sample=False,
                num_beams=self.config.blip_num_beams,
                max_length=self.config.blip_max_length,
                min_length=5
            )
        if self.config.blip_offload:
            self.blip_model = self.blip_model.to("cpu")
        return caption[0]


@atexit.register
def torch_done():
    torch.cuda.empty_cache()
