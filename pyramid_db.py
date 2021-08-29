import configparser
import sqlalchemy as db
import datetime
from sqlalchemy.orm import backref
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.schema import MetaData


Base = db.orm.declarative_base(metadata=MetaData(schema='season1'))

pyramid_owner_xref = db.Table(
    "pyramid_owner_xref",
    Base.metadata,
    db.Column("chatter_id", db.Integer, db.ForeignKey('chatter.id')),
    db.Column("pyramid_id", db.Integer, db.ForeignKey('pyramid.id')),
    schema='season1'
)


class Pyramid(Base):
    __tablename__ = 'pyramid'
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.Integer)
    channel = db.Column(db.String)
    points = db.Column(db.Integer)
    owners = db.orm.relationship('Chatter',
                                 secondary=pyramid_owner_xref,
                                 backref=backref('pyramids', lazy='dynamic'),
                                 lazy='dynamic'
                                )
    emote = db.Column(db.String)
    stolen_from_id = db.Column(db.Integer, db.ForeignKey('chatter.id'))
    stolen_by_id = db.Column(db.Integer, db.ForeignKey('chatter.id'))
    griefed_by_id = db.Column(db.Integer, db.ForeignKey('chatter.id'))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Chatter(Base):
    __tablename__ = 'chatter'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, index=True)
    stolen_from = db.orm.relationship('Pyramid', backref='stolen_from', primaryjoin='Pyramid.stolen_from_id==Chatter.id')
    stolen_by = db.orm.relationship('Pyramid', backref='stolen_by', primaryjoin='Pyramid.stolen_by_id==Chatter.id')
    griefed_by = db.orm.relationship('Pyramid', backref='griefed_by', primaryjoin='Pyramid.griefed_by_id==Chatter.id')
    points = db.orm.relationship('Points', backref='chatter', primaryjoin='Points.chatter_id==Chatter.id')

class Points(Base):
    __tablename__= 'points'
    id = db.Column(db.Integer, primary_key=True)
    chatter_id = db.Column(db.Integer, db.ForeignKey('chatter.id'))
    channel = db.Column(db.String, index=True)
    points = db.Column(db.Integer)

config = configparser.ConfigParser()
config.read('config.ini')
engine = db.create_engine(config['Database']['database_string'], echo = True)
Base.metadata.create_all(engine)
engine.dispose()

class PyramidDb():

    def __init__(self):
        engine = db.create_engine(config['Database']['database_string'], echo = True)
        Session = db.orm.sessionmaker(bind=engine)
        self.session = Session()
        self.session.execute("SET search_path TO season1")


    async def get_leaderboard(self, channel, griefer):
        if griefer:
            leaders = self.session.query(Points).filter(Points.channel==channel).order_by(Points.points).all()
        else:
            leaders = self.session.query(Points).filter(Points.channel==channel).order_by(Points.points.desc()).all()

        return leaders


    async def get_chatter_points(self, username, channel):
        chatter_points = self.session.query(Points).join(Chatter).filter(Chatter.name==username, Points.channel==channel).first()
        chatter = self.session.query(Chatter).filter_by(name=username).first()
        if chatter_points is not None: 
            return chatter_points, chatter
        else:
            points = Points(channel=channel, points = 0)
            chatter = Chatter(name=username)
            chatter.points.append(points)
            return points, chatter


    async def process_pyramid(self, messages, size, bot):
        score = size
        multiplier = 1
        if not (messages[0].content == messages[-1].content and len(messages) == (2*size-1)):
            if len(messages) < 4 or messages[0].author.name == messages[-1].author.name: return

            score = len(messages) - 2
            griefer = [messages[-1]]
            griefer_db = await self.get_chatter_points(griefer[0].author.name, griefer[0].channel.name)
            owner_set = {s.author.name for s in messages[:-1]}

            if (messages[0].author.is_mod or 'vip' in messages[0].author.badges.keys()) and len(owner_set) == 1 and messages[0].author.name != 'zoxkz':
                await bot.send_wrapper(griefer[0].channel.send, f'It\'s okay to grief {messages[0].author.name}\'s Mod/Broadcaster/VIP pyramid Okayge {griefer[0].author.name} got {score*multiplier} points')
            else:
                if griefer[0].author.name in {'icandyyyy', 'icandyyyy2', 'icandyyyy12', 'bigbenwd', 'hinoyy', 'emilyywang'} or griefer_db[0].points < -50:
                    multiplier *= 10000
                multiplier *= -1
                await bot.send_wrapper(griefer[0].channel.send, f'@{griefer[0].author.name} Madge {multiplier*score} pyramid points for griefing PeepoFinger .')
                await griefer[0].channel.timeout(griefer[0].author.name, bot.timeout_time, 'Griefed a pyramid')


            owners = [await self.get_chatter_points(owner, griefer[0].channel.name) for owner in owner_set]
            owners = [owner[1] for owner in owners]
            griefer_db[0].points += multiplier*score
            if griefer_db[0].points <= -4000000:
                griefer_db[0].points = 0
            self.session.add_all([griefer_db[0], griefer_db[1]])
            pyramid_record = Pyramid(size=size, channel=messages[0].channel.name, owners=owners, emote=messages[0].content, points=multiplier*score)
            pyramid_record.griefed = griefer_db[1]
            self.session.add_all(owners)
            self.session.add(pyramid_record)
        elif len({s.author.name for s in messages[:-1]}) == 1 and messages[0].author.name != messages[-1].author.name:
            stolen = messages[0]
            stealer = messages[-1]
            await bot.send_wrapper(stolen.channel.send, f'MadgeClap @{stealer.author.name} got 1 point for YOINKing. @{multiplier*stolen.author.name} still got {multiplier*score - 1} pyramid points Okayge .')
            stolen = await self.get_chatter_points(stolen.author.name, stolen.channel.name)
            stolen[0].points += multiplier*score - 1
            stealer = await self.get_chatter_points(stealer.author.name, stealer.channel.name)
            stealer[0].points += 1
            pyramid_record = Pyramid(size=size, channel=messages[0].channel.name, owners=[stolen[1], stealer[1]], emote=messages[0].content, points=multiplier*score)
            pyramid_record.stolen_from = stolen[1]
            pyramid_record.stolen_by = stealer[1]
            self.session.add_all(stolen)
            self.session.add_all(stealer)
            self.session.add(pyramid_record)
        elif len({s.author.name for s in messages}) > 1:
            team = {s.author.name for s in messages}
            multiplier *= len(team) * 0.76
            credit = ''
            for member in team:
                credit += f', {member}'
            credit = credit[2:]
            await bot.send_wrapper(messages[0].channel.send, f'peepoClap Teamwork! {credit} all got {round(score*multiplier)} pyramid points.')
            owners = [await self.get_chatter_points(name, messages[0].channel.name) for name in team]
            owners_chatters = [owner[1] for owner in owners]
            pyramid_record = Pyramid(size=size, channel=messages[0].channel.name, owners=owners_chatters, emote=messages[0].content, points=round(multiplier*score))
            for owner in owners:
                owner[0].points += round(score*multiplier)
            self.session.add(pyramid_record)
            for owner in owners:
                self.session.add_all(owner)
        else:
            if messages[0].author.name in {'icandyyyy', 'icandyyyy2', 'icandyyyy12', 'bigbenwd', 'hinoyy', 'emilyywang'}:
                multiplier = -10000  #KEKW

            await bot.send_wrapper(messages[0].channel.send, f'peepoClap nice {score}-wide @{messages[0].author.name}. You got {round(score*multiplier)} pyramid points for that one.')
            chatter = await self.get_chatter_points(messages[0].author.name, messages[0].channel.name)
            chatter[0].points += round(score * multiplier)
            if chatter[0].points <= -4000000:
                chatter[0].points = 0
            pyramid_record = Pyramid(size=size, channel=messages[0].channel.name, owners=[chatter[1]], emote=messages[0].content, points=round(multiplier*score))
            self.session.add_all([chatter[0], chatter[1]])
            self.session.add(pyramid_record)

        self.session.commit()

