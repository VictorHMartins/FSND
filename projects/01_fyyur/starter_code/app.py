#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import itertools
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.orm import validates
from sys import exc_info
from collections import Counter


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Created Venue Table with relations to Artist table.
class Venue(db.Model):
  __tablename__ = 'venue'

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(2), nullable=False)
  address = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  upcoming_shows = db.Column(db.Integer)
  artist = db.relationship('Artist', secondary='artist_venue', backref=db.backref('venue'))
  show = db.relationship('Show', backref=db.backref('venue'))
  

# Created Artist, child relation to Venue table.
class Artist(db.Model):
  __tablename__ = 'artist'

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  name = db.Column(db.String, nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(2), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(500))
  

  
# Creates the relationship between both Artists and Venues.
artist_venue = db.Table('artist_venue',
  db.Column('id', db.Integer, primary_key=True, nullable=False),
  db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), nullable=False),
  db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), nullable=False)
  )


# Created Genre wBeing the parent to both Artist and Venue: m::m
class Genre(db.Model):
  __tablename__ = 'genre'

  id = db.Column(db.Integer, primary_key=True, nullable=False)
  genre = db.Column(db.String(120),nullable=False)
  artist = db.relationship('Artist', secondary='artist_genre', backref=db.backref('genre'))
  venue = db.relationship('Venue', secondary='venue_genre', backref=db.backref('genre'))


# Association table for Artist and Genre
artist_genre = db.Table('artist_genre',
  db.Column('id', db.Integer, primary_key=True, nullable=False),
  db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), nullable=False),
  db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), nullable=False)
)


# Association table for Venue and Genre
venue_genre = db.Table('venue_genre',
  db.Column('id', db.Integer, primary_key=True, nullable=False),
  db.Column('venue_id', db.Integer, db.ForeignKey('venue.id'), nullable=False),
  db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), nullable=False)
)


# Created Show to relate both Artist and Venues, however it itself would store
# IDs so that it can identify the shows to its parents.
class Show(db.Model):
  __tablename__ = 'show'

  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime, nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
  artist = db.relationship('Artist', backref=db.backref('show'))





#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  
  try:

    data = []
    venue = db.session.query(Venue).all()
    show = db.session.query(Venue.id, Venue.name, Show.start_time).join(Venue.show).filter(Venue.id == Show.venue_id).all()

    show_data = []
    for s in show:
      temp = {"id": s.id, "name": s.name, "start_time": s.start_time 
      }
      show_data.append(temp)
    
    
    occurence = Counter([k['id'] for k in show_data if k.get('id')])
    common = dict(occurence.most_common())


    data = []
    for d in venue:
      temp = {"city": d.city, "state": d.state, "venues": [{
        "id": d.id, "name": d.name, "num_upcoming_shows": 0
        }]
      }
      data.append(temp)


    for v in data:        
      for venue in v['venues']:
        if venue['id'] in common:
          venue['num_upcoming_shows'] = common[venue['id']]
  
  except:
      db.session.rollback()
      db.session.close()
      flash('Venue ' + request.form['name'] + ' Had an issue pulling data')
      return render_template(redirect(url_for('venues')))


  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
 
  venue = db.session.query(Venue).filter(Venue.id == venue_id).all()
  genres = db.session.query(Genre.genre).join(Venue.genre).filter(Venue.id == venue_id).all()

  g = []
  for i in genres:     
    for x in i:
      g.append(x)
  
  for s in venue:
    venue_data = {"id": s.id, "name": s.name, "genres": g, "address": s.address, "city": s.city,
    "state": s.state, "phone": s.phone, "facebook_link": s.facebook_link}

  
  

  data = list(filter(lambda d: d['id'] == venue_id, [venue_data]))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  try:
    error = False
    genre = request.form.getlist('genres') # Takes Genres from the ImuutableDict
    data = {}
    for (k, v) in request.form.items(): # Obtains the rest of the entries.
      data[k] = v
    
    # Creates Venue with gathered data from above.
    venue = Venue(name=data['name'], city=data['city'], state=data['state'],
      address=data['address'], phone=data['phone'], facebook_link=data['facebook_link'])
    
    # Adds Venue to Model
    db.session.add(venue)

    # For each genre it associates each with the Venue.
    for g in genre:
      genre_title = db.session.query(Genre).filter(Genre.genre == g).first()
      venue.genre.append(genre_title)
    
    # Comming the additions
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

    # If any exceptions are raised it will flash an error on screen.
  except:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')


  return render_template('pages/home.html')



@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  data = []
  query = db.session.query(Artist).all()
  for d in query:
    artistDict = {"id":d.id, "name":d.name}
    data.append(artistDict)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 4,
  #     "name": "Guns N Petals",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  query = db.session.query(Artist).all()
  artist = []

  # It'll cycle through the selected IDs obj 
  # and send the artist object back in the response.
  for d in query:
    artistDict = {"id":d.id, "name":d.name, "city":d.city, "state":d.state,
    "phone":d.phone, "image_link":d.image_link, "facebook_link":d.facebook_link}
    artist.append(artistDict)
  
  
  data = list(filter(lambda d: d['id'] == artist_id, artist))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = db.session.query(Artist).get(artist_id)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  error = False
  genre = request.form.getlist('genres') # Takes Genres from the ImuutableDict
  fetched_artist = {}
  
  for (k, v) in request.form.items(): # Obtains the rest of the entries.
    fetched_artist[k] = v

  artist = db.session.query(Artist).get(artist_id)
  artist.name = fetched_artist['name']
  artist.city = fetched_artist['city']
  artist.state = fetched_artist['state']
  artist.phone = fetched_artist['phone']
  artist.facebook_link = fetched_artist['facebook_link']
    
  db.session.commit()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # Initial start to entering data into Artists and Genres tables.
  try:
    error = False
    genre = request.form.getlist('genres') # Takes Genres from the ImuutableDict
    data = {}
    for (k, v) in request.form.items(): # Obtains the rest of the entries.
      data[k] = v
    
    # Creates Artist with gathered data from above.
    artist = Artist(name=data['name'], city=data['city'], state=data['state'],
      phone=data['phone'], facebook_link=data['facebook_link'])
    
    # Adds artist to Model
    db.session.add(artist)

    # For each genre it associates each with the Artist.
    for g in genre:
      genre_title = db.session.query(Genre).filter(Genre.genre == g).first()
      artist.genre.append(genre_title)
    
    
    db.session.commit()
    db.session.close()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')


  except:
    error = True
    db.session.rollback()
    db.session.close()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')


  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
 
  try:
    error = False
    data = {} # Takes Shows from the ImuutableDict
    for (k, v) in request.form.items(): # Obtains the rest of the entries.
      data[k] = v

    # Creates Show with gathered data from above.
    show = Show(artist_id=data['artist_id'], venue_id=data['venue_id'], start_time=data['start_time'] )
    db.session.add(show)

    db.session.commit()
    db.session.close()

    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    db.session.close()
    error = True
    flash('Show has failed to be listed! Please check connection!')


  return render_template('pages/home.html')



@app.errorhandler(404)
def not_found_error(error):
  return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
  return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
