from typing import Optional

from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class NiveauSponsor(Base):
    __tablename__ = "niveaux_sponsor"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String(50), nullable=False)
    ordre_affichage: Mapped[int] = mapped_column(Integer, default=0)
    couleur: Mapped[str | None] = mapped_column(String(7), nullable=True)

    sponsors: Mapped[list["Sponsor"]] = relationship("Sponsor", back_populates="niveau")


class Sponsor(Base):
    __tablename__ = "sponsors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String(150), nullable=False)
    logo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    lien_site: Mapped[str] = mapped_column(String(500), nullable=False)
    niveau_id: Mapped[int] = mapped_column(ForeignKey("niveaux_sponsor.id"), nullable=False, index=True)

    niveau: Mapped["NiveauSponsor"] = relationship("NiveauSponsor", back_populates="sponsors")