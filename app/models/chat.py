from app import db
from datetime import datetime
import pytz
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    resolved = db.Column(db.Boolean, default=True)

    messages = db.relationship('Message', backref='chat', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'resolved': self.resolved
        }

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc))
    is_admin = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'is_admin': self.is_admin
        }
