from app import db
import datetime
class ReferenceFile(db.Model):
    uuid = db.Column(db.String(64), primary_key=True)
    reference_pdf_name = db.Column(db.String(64), nullable=False)
    reference_pdf = db.Column(db.LargeBinary, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    
    def __repr__(self):
        return '<UUID {}>'.format(self.uuid)

class OriginalFile(db.Model):
    uuid = db.Column(db.String(64), primary_key=True)
    original_pdf_name = db.Column(db.String(64), nullable=False)
    original_pdf = db.Column(db.LargeBinary, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    uuid_ref = db.Column(db.String(64), nullable=False)
    
    def __repr__(self):
        return '<UUID {}>'.format(self.uuid)

class ReferenceFileRegex(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    regex = db.Column(db.String(250), nullable=False)
    uuid_ref = db.Column(db.String(64), nullable=False) 
    
    def __repr__(self):
        return '<ID {}>'.format(self.id)