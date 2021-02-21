import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms

from modules import SPADEResnetBlock

class Generator(nn.Module):
    
    def __init__(self, latent_dim, n_classes, hidden_dims):
        super().__init__()
        # self.fc1 = nn.Linear(in_features=latent_dim, out_features=hidden_dim)
        # self.fc2 = nn.Linear(in_features=hidden_dim, out_features=output_dim)
        self.hidden_dims = hidden_dims 
        self.conv1 = nn.Conv2d(in_channels=latent_dim+n_classes, out_channels=hidden_dims[0], kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(in_channels=hidden_dims[-1], out_channels=3, kernel_size=3, padding=1)
        self.spade_blocks = nn.ModuleList([
            SPADEResnetBlock(fin=hidden_dims[0], fout=hidden_dims[0], in_channels_label=latent_dim+n_classes)
        ])
        for hin, hout in zip(hidden_dims[:-1], hidden_dims[1:]):
            self.spade_blocks.append(
                SPADEResnetBlock(fin=hin, fout=hout, in_channels_label=latent_dim+n_classes)
            )
        
    def forward(self, z, y):
        """
        z: 3D Noise: (batch_size, 64, height, width)
        y: label map: (batch_size, N, height, width)
        """
        # (1) concatenate input noise with label map
        zy = torch.cat([z, y], dim=1)

        # (2) downsample via interpolate
        zy1 = F.interpolate(zy, scale_factor=1/32, mode='nearest') # (batch_size, N+64, 8, 8), same mode used in SPADE

        # (3) First Convolution
        x = self.conv1(zy1)

        # (3) SPADE Resnet Blocks
        x = self.spade_blocks[0](x, zy1)
        x = F.interpolate(x, scale_factor=2, mode='nearest')

        # (3) SPADE Resnet Blocks
        zy2 = F.interpolate(zy, scale_factor=1/16, mode='nearest')
        x = self.spade_blocks[1](x, zy2)
        x = F.interpolate(x, scale_factor=2, mode='nearest')
        
        # (4) SPADE Resnet Blocks
        zy3 = F.interpolate(zy, scale_factor=1/8, mode='nearest')
        x = self.spade_blocks[2](x, zy3)
        x = F.interpolate(x, scale_factor=2, mode='nearest')
        
        # (5) SPADE Resnet Blocks
        zy3 = F.interpolate(zy, scale_factor=1/4, mode='nearest')
        x = self.spade_blocks[3](x, zy3)
        x = F.interpolate(x, scale_factor=2, mode='nearest')
        
        # (6) SPADE Resnet Blocks
        zy3 = F.interpolate(zy, scale_factor=1/2, mode='nearest')
        x = self.spade_blocks[4](x, zy3)
        x = F.interpolate(x, scale_factor=2, mode='nearest')

        # (7) Final convolutional layer
        x = self.conv2(x)
        x = torch.tanh(F.leaky_relu(x, 2e-1))

        return x