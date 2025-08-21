from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PrayerTimes(db.Model):
    __tablename__ = "prayer_times"

    mosque_name = db.Column(db.String, primary_key=True)
    date = db.Column(db.Date, nullable=False)

    fajr_start = db.Column(db.Time, nullable=True)
    fajr_iqamah = db.Column(db.Time, nullable=True)

    zuhr_start = db.Column(db.Time, nullable=True)
    zuhr_iqamah = db.Column(db.Time, nullable=True)

    asr_start = db.Column(db.Time, nullable=True)
    asr_iqamah = db.Column(db.Time, nullable=True)

    maghrib_start = db.Column(db.Time, nullable=True)
    maghrib_iqamah = db.Column(db.Time, nullable=True)

    isha_start = db.Column(db.Time, nullable=True)
    isha_iqamah = db.Column(db.Time, nullable=True)

    jummah1_start = db.Column(db.Time, nullable=True)
    jummah1_iqamah = db.Column(db.Time, nullable=True)

    jummah2_start = db.Column(db.Time, nullable=True)
    jummah2_iqamah = db.Column(db.Time, nullable=True)

    jummah3_start = db.Column(db.Time, nullable=True)
    jummah3_iqamah = db.Column(db.Time, nullable=True)

    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        """Serialize to dict for JSON responses."""
        return {
            "mosque_name": self.mosque_name,
            "date": self.date.isoformat(),
            "fajr_start": str(self.fajr_start) if self.fajr_start else None,
            "fajr_iqamah": str(self.fajr_iqamah) if self.fajr_iqamah else None,
            "zuhr_start": str(self.zuhr_start) if self.zuhr_start else None,
            "zuhr_iqamah": str(self.zuhr_iqamah) if self.zuhr_iqamah else None,
            "asr_start": str(self.asr_start) if self.asr_start else None,
            "asr_iqamah": str(self.asr_iqamah) if self.asr_iqamah else None,
            "maghrib_start": str(self.maghrib_start) if self.maghrib_start else None,
            "maghrib_iqamah": str(self.maghrib_iqamah) if self.maghrib_iqamah else None,
            "isha_start": str(self.isha_start) if self.isha_start else None,
            "isha_iqamah": str(self.isha_iqamah) if self.isha_iqamah else None,
            "jummah1_start": str(self.jummah1_start) if self.jummah1_start else None,
            "jummah1_iqamah": str(self.jummah1_iqamah) if self.jummah1_iqamah else None,
            "jummah2_start": str(self.jummah2_start) if self.jummah2_start else None,
            "jummah2_iqamah": str(self.jummah2_iqamah) if self.jummah2_iqamah else None,
            "jummah3_start": str(self.jummah3_start) if self.jummah3_start else None,
            "jummah3_iqamah": str(self.jummah3_iqamah) if self.jummah3_iqamah else None,
            "updated_at": self.updated_at.isoformat(),
        }
