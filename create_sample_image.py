"""Create a simple placeholder image (cat.png) for testing app.py.

Requires Pillow: pip install pillow
"""

from PIL import Image, ImageDraw

WIDTH, HEIGHT = 768, 768


def main() -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), "#f7e7ce")
    draw = ImageDraw.Draw(img)

    # A very rough "cat" so there is something to animate.
    draw.ellipse((180, 300, 588, 640), fill="#8d6e63")  # body
    draw.ellipse((250, 180, 518, 430), fill="#a1887f")  # head
    draw.polygon([(270, 220), (330, 120), (400, 210)], fill="#a1887f")  # left ear
    draw.polygon([(370, 210), (440, 120), (500, 220)], fill="#a1887f")  # right ear
    draw.ellipse((315, 290, 355, 330), fill="#212121")  # left eye
    draw.ellipse((415, 290, 455, 330), fill="#212121")  # right eye
    draw.polygon([(370, 350), (400, 350), (385, 375)], fill="#ff8a80")  # nose

    img.save("cat.png")
    print("Wrote cat.png")


if __name__ == "__main__":
    main()
