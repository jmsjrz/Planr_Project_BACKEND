from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile

def process_image(image, max_size=(800, 800), quality=80):
    img = Image.open(image)
    img = img.convert('RGB') # Pour éviter les problèmes avec les images PNG transparentes
    output = io.BytesIO()
    img.thumbnail(max_size)  # Redimensionner l'image
    img.save(output, format='JPEG', quality=quality)  # Compression de l'image
    output.seek(0)
    
    return InMemoryUploadedFile(
        output, 'ImageField', f"{image.name.split('.')[0]}.jpg", 'image/jpeg', output.getbuffer().nbytes, None
    )
