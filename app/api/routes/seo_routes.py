import io
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image, ImageDraw, ImageFont

from app.core.deps import get_db
from app.repositories.concept_repository import ConceptRepository
from app.repositories.mathematicien_repository import MathematicienRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.type_repository import TypeRepository
from app.core.config import settings

router = APIRouter(prefix="/seo", tags=["seo"])


@router.get("/sitemap.xml", summary="Generate dynamic sitemap")
async def generate_sitemap(db: AsyncSession = Depends(get_db)):
    base_url = settings.NEW_FRONTEND_URL.rstrip("/")

    concept_repo = ConceptRepository(db)
    concepts = await concept_repo.get_all_concepts_name()

    math_repo = MathematicienRepository(db)
    maths = await math_repo.get_all()

    cat_repo = CategoryRepository(db)
    cats = await cat_repo.get_all()

    type_repo = TypeRepository(db)
    types = await type_repo.get_all()

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    # Home Page
    xml.append(f"  <url><loc>{base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>")
    xml.append(f"  <url><loc>{base_url}/about</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>")
    xml.append(f"  <url><loc>{base_url}/search</loc><changefreq>daily</changefreq><priority>0.8</priority></url>")
    xml.append(
        f"  <url><loc>{base_url}/mathematiciens</loc><changefreq>daily</changefreq><priority>0.8</priority></url>"
    )

    for c in concepts:
        xml.append(
            f"  <url><loc>{base_url}/concept/{c.id}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>"
        )

    for m in maths:
        xml.append(
            f"  <url><loc>{base_url}/mathematicien/{m.id}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>"
        )

    for c in cats:
        xml.append(
            f"  <url><loc>{base_url}/category/{c.id}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>"
        )

    for t in types:
        xml.append(
            f"  <url><loc>{base_url}/type/{t.id}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>"
        )

    xml.append("</urlset>")

    return Response(content="\\n".join(xml), media_type="application/xml")


@router.get("/share-image/concept/{concept_id}", summary="Generate OG Image for Concept")
async def generate_share_image(concept_id: int, db: AsyncSession = Depends(get_db)):
    repo = ConceptRepository(db)
    concept = await repo.get_concept_by_id(concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Création d'une image standard pour OpenGraph (1200x630)
    img = Image.new("RGB", (1200, 630), color=(17, 24, 39))  # Gris très sombre
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.load_default(size=64)
        font_sub = ImageFont.load_default(size=32)
    except Exception:
        # Fallback pour les anciennes versions de Pillow si besoin
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    text = concept.nom
    bbox = draw.textbbox((0, 0), text, font=font_title)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    # Dessiner le titre au centre
    draw.text(((1200 - w) / 2, (630 - h) / 2 - 20), text, font=font_title, fill=(243, 244, 246))

    subtitle = "MathGraph - Explorateur de mathématiques"
    bbox_sub = draw.textbbox((0, 0), subtitle, font=font_sub)
    w_sub = bbox_sub[2] - bbox_sub[0]
    draw.text(((1200 - w_sub) / 2, (630 - h) / 2 + 80), subtitle, font=font_sub, fill=(156, 163, 175))

    # Rendu
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    return Response(content=img_byte_arr.getvalue(), media_type="image/png")


def create_image_for_text(text: str, subtitle: str) -> Response:
    img = Image.new("RGB", (1200, 630), color=(17, 24, 39))
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.load_default(size=64)
        font_sub = ImageFont.load_default(size=32)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font_title)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((1200 - w) / 2, (630 - h) / 2 - 20), text, font=font_title, fill=(243, 244, 246))

    bbox_sub = draw.textbbox((0, 0), subtitle, font=font_sub)
    w_sub = bbox_sub[2] - bbox_sub[0]
    draw.text(((1200 - w_sub) / 2, (630 - h) / 2 + 80), subtitle, font=font_sub, fill=(156, 163, 175))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return Response(content=img_byte_arr.getvalue(), media_type="image/png")


@router.get("/share-image/mathematicien/{math_id}", summary="Generate OG Image for Mathematicien")
async def generate_math_image(math_id: int, db: AsyncSession = Depends(get_db)):
    repo = MathematicienRepository(db)
    math = await repo.get_by_id(math_id)
    if not math:
        raise HTTPException(status_code=404, detail="Mathematicien not found")
    return create_image_for_text(math.nom, "MathGraph - Explorateur de mathématiques")


@router.get("/share-image/category/{cat_id}", summary="Generate OG Image for Category")
async def generate_cat_image(cat_id: int, db: AsyncSession = Depends(get_db)):
    repo = CategoryRepository(db)
    cat = await repo.get_by_id(cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return create_image_for_text(cat.nom, "MathGraph - Catégorie")


@router.get("/share-image/type/{type_id}", summary="Generate OG Image for Type")
async def generate_type_image(type_id: int, db: AsyncSession = Depends(get_db)):
    repo = TypeRepository(db)
    t = await repo.get_by_id(type_id)
    if not t:
        raise HTTPException(status_code=404, detail="Type not found")
    return create_image_for_text(t.type, "MathGraph - Type de concept")
