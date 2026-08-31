import os
from PIL import Image, ImageEnhance, ImageFilter
from pyrogram import Client, filters


DOWNLOAD_DIR = "downloads"

# Make sure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def get_replied_photo(client, message):
    """Get the photo that the user replied to."""
    if not message.reply_to_message:
        return None

    replied = message.reply_to_message

    if replied.photo:
        return replied

    # Also allow an image sent as a document
    if replied.document:
        mime = replied.document.mime_type or ""
        file_name = replied.document.file_name or ""

        if mime.startswith("image/") or file_name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):
            return replied

    return None


@Client.on_message(
    filters.private & filters.command("upscale")
)
async def upscale_image(client, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "**Reply to an image with `/upscale` ❌**"
        )

    replied = await get_replied_photo(client, message)

    if not replied:
        return await message.reply_text(
            "**Please reply to an image/photo with `/upscale` ❌**"
        )

    status = await message.reply_text(
        "**Downloading image... 📥**"
    )

    input_file = None
    output_file = None

    try:
        input_file = await client.download_media(
            replied,
            file_name=os.path.join(DOWNLOAD_DIR, "upscale_input")
        )

        if not input_file:
            return await status.edit(
                "**Failed to download the image ❌**"
            )

        output_file = os.path.join(
            DOWNLOAD_DIR,
            f"upscaled_{message.from_user.id}.jpg"
        )

        image = Image.open(input_file)

        # Convert to RGB for JPEG output
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # 2x upscale
        new_size = (
            image.width * 2,
            image.height * 2
        )

        image = image.resize(
            new_size,
            Image.Resampling.LANCZOS
        )

        # Slight sharpening after upscale
        image = image.filter(
            ImageFilter.UnsharpMask(
                radius=1.5,
                percent=120,
                threshold=3
            )
        )

        image.save(
            output_file,
            "JPEG",
            quality=95,
            optimize=True
        )

        await status.edit(
            "**Uploading upscaled image... 📤**"
        )

        await client.send_photo(
            chat_id=message.chat.id,
            photo=output_file,
            caption=(
                "**Upscaled Successfully ✅**\n\n"
                f"**Original:** `{image.width // 2} × {image.height // 2}`\n"
                f"**New:** `{image.width} × {image.height}`"
            )
        )

        await status.delete()

    except Exception as e:
        await status.edit(
            f"**Upscale failed ❌**\n\n`{str(e)[:1000]}`"
        )

    finally:
        for file in (input_file, output_file):
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except Exception:
                    pass


@Client.on_message(
    filters.private & filters.command("enhance")
)
async def enhance_image(client, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "**Reply to an image with `/enhance` ❌**"
        )

    replied = await get_replied_photo(client, message)

    if not replied:
        return await message.reply_text(
            "**Please reply to an image/photo with `/enhance` ❌**"
        )

    status = await message.reply_text(
        "**Downloading image... 📥**"
    )

    input_file = None
    output_file = None

    try:
        input_file = await client.download_media(
            replied,
            file_name=os.path.join(DOWNLOAD_DIR, "enhance_input")
        )

        if not input_file:
            return await status.edit(
                "**Failed to download the image ❌**"
            )

        output_file = os.path.join(
            DOWNLOAD_DIR,
            f"enhanced_{message.from_user.id}.jpg"
        )

        image = Image.open(input_file)

        # Convert to RGB
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Improve image
        image = ImageEnhance.Contrast(image).enhance(1.12)
        image = ImageEnhance.Sharpness(image).enhance(1.5)
        image = ImageEnhance.Color(image).enhance(1.05)

        # Small sharpening pass
        image = image.filter(
            ImageFilter.UnsharpMask(
                radius=1.2,
                percent=100,
                threshold=3
            )
        )

        image.save(
            output_file,
            "JPEG",
            quality=95,
            optimize=True
        )

        await status.edit(
            "**Uploading enhanced image... 📤**"
        )

        await client.send_photo(
            chat_id=message.chat.id,
            photo=output_file,
            caption="**Image Enhanced Successfully ✅**"
        )

        await status.delete()

    except Exception as e:
        await status.edit(
            f"**Enhancement failed ❌**\n\n`{str(e)[:1000]}`"
        )

    finally:
        for file in (input_file, output_file):
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except Exception:
                    pass
