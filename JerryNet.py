import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

# Define the CNN block with ResNet
class CNNBlock(nn.Module):
    def __init__(self, in_channels):
        super(CNNBlock, self).__init__()
        # Using a pre-trained ResNet block for feature extraction
        resnet = models.resnet18(pretrained=True)
        self.resnet_layers = nn.Sequential(*(list(resnet.children())[:-2]))  # Removing the final classification layers
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.pool(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = self.pool(x)
        x = self.resnet_layers(x)  # Extract features with ResNet
        return x

# Define the Transformer block
class TransformerBlock(nn.Module):
    def __init__(self, embed_size, heads, forward_expansion, dropout, num_layers):
        super(TransformerBlock, self).__init__()
        self.embed_size = embed_size
        self.transformer = nn.Transformer(
            d_model=embed_size, 
            nhead=heads, 
            num_encoder_layers=num_layers, 
            dim_feedforward=forward_expansion * embed_size, 
            dropout=dropout
        )
    
    def forward(self, x):
        return self.transformer(x, x)

# Define the complete sound localization model
class SoundLocalizationModel(nn.Module):
    def __init__(self, num_mics=4, num_classes=2, embed_size=256, heads=8, forward_expansion=4, dropout=0.1, num_layers=3):
        super(SoundLocalizationModel, self).__init__()
        
        # CNN blocks for each microphone input
        self.cnn_blocks = nn.ModuleList([CNNBlock(in_channels=1) for _ in range(num_mics)])
        
        # Transformer for capturing dependencies between microphone inputs
        self.transformer = TransformerBlock(embed_size, heads, forward_expansion, dropout, num_layers)
        
        # Fully connected layers for regression (outputting localization coordinates)
        self.fc = nn.Sequential(
            nn.Linear(embed_size * num_mics, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes)  # Output (e.g., azimuth and elevation coordinates)
        )

    def forward(self, x):
        # Assuming x is a list of inputs from each microphone
        mic_features = [cnn_block(mic_input) for cnn_block, mic_input in zip(self.cnn_blocks, x)]
        
        # Flatten the CNN outputs
        mic_features = [torch.flatten(f, start_dim=1) for f in mic_features]
        
        # Concatenate the features from all microphones
        concatenated = torch.cat(mic_features, dim=1)
        
        # Pass through transformer
        transformer_out = self.transformer(concatenated.unsqueeze(0))  # Add sequence length dimension
        
        # Remove sequence length dimension and pass through FC layers
        out = self.fc(transformer_out.squeeze(0))
        return out

# Create a model instance for 4 microphones
model = SoundLocalizationModel(num_mics=4, num_classes=2)
print(model)  # Visualize the model architecture
