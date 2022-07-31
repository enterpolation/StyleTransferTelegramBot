import torch
import torch.optim as optim
from PIL import Image
import torchvision.transforms as tt
from models import VGG, Generator

DEVICE = torch.device('cuda' if torch.cuda.is_available else 'cpu')


def load_image(image, imsize):
    transform = tt.Compose([
        tt.Resize((imsize, imsize)),
        tt.ToTensor(),
        # tt.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    image = Image.open(image)
    image = transform(image).unsqueeze(0)
    return image.to(DEVICE)


async def gan_transfer(user, original_img):
    IMAGE_SIZE = user.settings['imsize']

    model = Generator().to(DEVICE)
    model.load_state_dict(torch.load('./checkpoints/gen_M.pth'))

    original_img = load_image(original_img, IMAGE_SIZE)
    generated_img = model(original_img).cpu().detach()
    return generated_img


async def simple_transfer(user, style_img, original_img):
    LEARNING_RATE = 1e-3
    ALPHA = 1
    BETA = user.settings['style_coef']
    IMAGE_SIZE = user.settings['imsize']
    TOTAL_STEPS = user.settings['num_steps']

    original_img = load_image(original_img, IMAGE_SIZE)
    style_img = load_image(style_img, IMAGE_SIZE)

    model = VGG().to(DEVICE).eval()
    generated_img = original_img.clone().requires_grad_(True)
    optimizer = optim.Adam([generated_img], lr=LEARNING_RATE)

    for step in range(TOTAL_STEPS):
        generated_features = model(generated_img)
        original_features = model(original_img)
        style_features = model(style_img)

        style_loss = original_loss = 0

        for gen_feature, orig_feature, style_feature in zip(
                generated_features, original_features, style_features
        ):
            batch_size, channel, height, width = gen_feature.shape
            original_loss += torch.mean((gen_feature - orig_feature) ** 2)

            G = gen_feature.view(channel, height * width).mm(
                gen_feature.view(channel, height * width).t()
            )

            A = style_feature.view(channel, height * width).mm(
                style_feature.view(channel, height * width).t()
            )

            style_loss += torch.mean((G - A) ** 2)

        total_loss = ALPHA * original_loss + BETA * style_loss
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        if step % 50 == 0:
            print("Total loss: {loss:9.3f}".format(loss=total_loss.item()))

    return generated_img
