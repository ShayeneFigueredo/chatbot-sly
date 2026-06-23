#!/usr/bin/env python3
"""
Gera icones PWA com a logo da Sly Design em background gradiente roxo moderno.

Rode: python3 frontend/painel/generate_icons.py

Para usar icone customizado:
  Coloque um PNG (1024x1024, fundo transparente) em: frontend/painel/public/icons/icon-src.png
  Delete a logo baixada em cache e rode o script de novo.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import requests
from io import BytesIO

DEST = os.path.join(os.path.dirname(__file__), "public", "icons")
SRC = os.path.join(DEST, "icon-src.png")
LOGO_URL = "https://slydesign.com.br/wp-content/uploads/2025/08/branco-1.png"
LOGO_CACHE = os.path.join(DEST, ".logo-sly-cache.png")


def baixar_logo():
    """Baixa a logo oficial da Sly Design (ou usa cache)."""
    if os.path.exists(LOGO_CACHE):
        return Image.open(LOGO_CACHE).convert("RGBA")

    print("⬇️  Baixando logo oficial da Sly Design...")
    try:
        resp = requests.get(LOGO_URL, timeout=15)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGBA")
        img.save(LOGO_CACHE, "PNG")
        print(f"   Logo salva: {LOGO_CACHE}")
        return img
    except Exception as e:
        print(f"⚠️  Erro ao baixar logo: {e}")
        return None


def criar_fundo_gradiente(size):
    """Cria background roxo moderno com gradiente diagonal e brilho."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gradiente vertical suave: roxo escuro → roxo vibrante → lilas
    for y in range(size):
        t = y / size
        # 3 pontos de cor: #1a0533 → #7c3aed → #a78bfa
        if t < 0.5:
            s = t * 2  # 0..1
            r = int(26 + (124 - 26) * s)
            g = int(5 + (58 - 5) * s)
            b_val = int(51 + (237 - 51) * s)
        else:
            s = (t - 0.5) * 2  # 0..1
            r = int(124 + (167 - 124) * s)
            g = int(58 + (139 - 58) * s)
            b_val = int(237 + (250 - 237) * s)
        draw.line([(0, y), (size, y)], fill=(r, g, b_val, 255))

    # Brilho central (luz suave no meio)
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    cx, cy = size // 2, size // 2
    for i in range(6, 0, -1):
        radius = int(size * 0.7 * (i / 6))
        alpha = int(25 * (1 - i / 7))
        glow_draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(167, 139, 250, alpha)
        )
    img = Image.alpha_composite(img, glow)

    # Borda sutil (anel brilhante)
    margin = int(size * 0.025)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=int(size * 0.22),
        outline=(167, 139, 250, 60),
        width=max(2, int(size * 0.008))
    )

    return img


def criar_icone_com_logo(size, logo_img):
    """Cria icone final: fundo gradiente + logo centralizada."""
    # Fundo
    icon = criar_fundo_gradiente(size)

    # Redimensiona logo (ocupa ~55% do icone)
    logo_size = int(size * 0.55)
    logo_resized = logo_img.resize((logo_size, logo_size), Image.LANCZOS)

    # Centraliza
    offset_x = (size - logo_size) // 2
    offset_y = (size - logo_size) // 2

    # Sombra suave atras da logo (glow)
    shadow = Image.new("RGBA", (logo_size + int(size * 0.12), logo_size + int(size * 0.12)), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    for i in range(4, 0, -1):
        alpha = int(40 * (1 - i / 5))
        shadow_draw.ellipse(
            [int(size * 0.06 * i / 4), int(size * 0.06 * i / 4),
             logo_size + int(size * 0.06 * (1 - i / 4)), logo_size + int(size * 0.06 * (1 - i / 4))],
            fill=(255, 255, 255, alpha)
        )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=size * 0.025))

    shadow_offset_x = offset_x - int(size * 0.06)
    shadow_offset_y = offset_y - int(size * 0.06)
    icon.paste(shadow, (shadow_offset_x, shadow_offset_y), shadow)
    icon.paste(logo_resized, (offset_x, offset_y), logo_resized)

    return icon


def criar_splash_com_logo(width, height, scale, logo_img):
    """Cria tela splash iPhone com logo e gradiente sutil."""
    w, h = int(width * scale), int(height * scale)

    # Fundo escuro solido
    img = Image.new("RGB", (w, h), (9, 9, 13))

    # Gradiente sutil no topo
    draw = ImageDraw.Draw(img)
    bands = 60
    for i in range(bands):
        t = i / bands
        alpha_blend = t * 0.15
        r = int(9 + (124 - 9) * alpha_blend)
        g = int(9 + (58 - 9) * alpha_blend)
        b = int(13 + (237 - 13) * alpha_blend)
        y_start = int(i * h / bands)
        y_end = int((i + 1) * h / bands)
        draw.rectangle([0, y_start, w, y_end], fill=(r, g, b))

    # Logo centralizada (~22% da menor dimensao)
    logo_size = int(min(w, h) * 0.22)
    logo_resized = logo_img.resize((logo_size, logo_size), Image.LANCZOS)

    lx = (w - logo_size) // 2
    ly = int(h * 0.3)
    img_rgba = img.convert("RGBA")
    # Aplica alpha na logo (90% opacidade)
    logo_with_alpha = logo_resized.copy()
    logo_with_alpha.putalpha(int(255 * 0.9))
    img_rgba.paste(logo_with_alpha, (lx, ly), logo_with_alpha)

    # Linha decorativa sutil abaixo da logo
    img_rgba = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img_rgba)
    line_y = ly + logo_size + int(h * 0.045)
    line_w = logo_size * 0.5
    line_x = (w - line_w) // 2
    draw.rounded_rectangle(
        [line_x, line_y, line_x + line_w, line_y + max(2, int(h * 0.003))],
        radius=2,
        fill=(167, 139, 250)
    )

    return img_rgba


if __name__ == "__main__":
    os.makedirs(DEST, exist_ok=True)

    # Se tem icone personalizado, usa ele
    if os.path.exists(SRC):
        print("🎨 Usando icone personalizado: icon-src.png")
        logo = Image.open(SRC).convert("RGBA")
    else:
        logo = baixar_logo()
        if logo is None:
            print("❌ Nao foi possivel obter a logo. Abortando.")
            sys.exit(1)

    print()

    # Gera icones PWA
    for label, size in [("192", 192), ("512", 512)]:
        path = os.path.join(DEST, f"icon-{size}.png")
        if os.path.exists(SRC):
            img = Image.open(SRC).convert("RGBA")
            img = img.resize((size, size), Image.LANCZOS)
        else:
            img = criar_icone_com_logo(size, logo)
        img.save(path, "PNG")
        print(f"✅ icon-{size}.png ({size}x{size})")

    # Splash screens
    splash_1170 = criar_splash_com_logo(390, 844, 3, logo)
    splash_1170.save(os.path.join(DEST, "splash-1170.png"), "PNG")
    print("✅ splash-1170.png (1170x2532 — iPhone Pro)")

    splash_1290 = criar_splash_com_logo(430, 932, 3, logo)
    splash_1290.save(os.path.join(DEST, "splash-1290.png"), "PNG")
    print("✅ splash-1290.png (1290x2796 — iPhone Pro Max)")

    print()
    if not os.path.exists(SRC):
        print("💡 Para usar seu proprio icone:")
        print(f"   Coloque um PNG em: {SRC}")
        print("   (recomendado 1024x1024, fundo transparente)")
        print("   Depois rode este script de novo.")
    print()
    print("📱 Agora faca o build:")
    print("   cd frontend/painel && npm run build")
