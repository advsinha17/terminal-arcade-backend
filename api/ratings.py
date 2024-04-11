from fastapi import APIRouter
from firebase_admin import storage
from firebase_config import db 
from pydantic import BaseModel
from api.creator_leaderboard import update_creator_leaderboard
from api.player_leaderboard import update_player_leaderboard

router = APIRouter()

class Rating(BaseModel):
    user_id: str
    game_id: str
    rating : int

class RatingCheck(BaseModel):
    user_id: str
    game_id: str

def check_if_rated(user_id, ratings_list):
    if ratings_list is not None:
        for _rating_doc in ratings_list:
            _rating_dict = [x for x in _rating_doc.values()][0]
            if _rating_dict["user_id"] == user_id:
                return True
    return False
                

@router.post("/ratings/rate")
async def rate(rating: Rating):
    if rating.rating < 1 or rating.rating > 5:
        return {"error": "Rating must be between 1 and 5"}
    game_ref = db.collection("games").document(rating.game_id)
    ratings_ref = game_ref.collection("ratings")
    ratings = ratings_ref.stream()
    all_ratings = [{document.id: document.to_dict()} for document in ratings]
    rating_exists = check_if_rated(rating.user_id, all_ratings)
    if rating_exists==False:
        db.collection("games").document(rating.game_id).collection("ratings").document().set({
            "game_id": rating.game_id,
            "user_id" : rating.user_id,
            "rating" : rating.rating
        })
        game = game_ref.get()
        if game.exists:
            game_data = game.to_dict()
            total_rating = game_data.get('total_rating', 0) + rating.rating
            number_of_ratings = game_data.get('number_of_ratings', 0) + 1
            game_ref.update({
                'total_rating': total_rating,
                'number_of_ratings': number_of_ratings
            })

            stats_ref = db.collection('game_stats').document('stats')
            stats = stats_ref.get()
            if stats.exists:
                stats_data = stats.to_dict()
                total_number_of_games = stats_data.get('number_of_games', 0)
                min_avg_playtime = stats_data.get('min_avg_playtime', 0)
                max_avg_playtime = stats_data.get('max_avg_playtime', 0)
                total_playtime_all_games = stats_data.get('total_playtime_all_games', 0)
                total_number_of_plays_all_games = stats_data.get('total_number_of_plays_all_games', 0)
                if total_number_of_games > 5 and total_number_of_plays_all_games > 5 and number_of_ratings > 0 and total_playtime_all_games > 0 and not max_avg_playtime == min_avg_playtime:
                    await update_creator_leaderboard(rating.game_id, total_rating, number_of_ratings, total_number_of_plays_all_games, total_playtime_all_games, max_avg_playtime, min_avg_playtime)

        print("going to update")
        await update_player_leaderboard(rating.user_id)
        return {"message": "rating written succesfully"}
    else:
        return {"error": "user has already rated the game"}

@router.get("/games/{game_id}/ratings")
async def fetch_ratings(game_id: str):
    ratings = db.collection("games").document(game_id).collection("ratings").stream()
    all_ratings = [{document.id: document.to_dict()} for document in ratings]
    if ratings is not None:
        return all_ratings 
    else:
        return {"message": "ratings unavailable"}
    

@router.get("/ratings/hasrated")
async def rated_by_user(ratingcheck: RatingCheck):
    ratings = db.collection("games").document(ratingcheck.game_id).collection("ratings").stream()
    all_ratings = [{document.id: document.to_dict()} for document in ratings]
    rating_exists = check_if_rated(ratingcheck.user_id, all_ratings)
    if rating_exists:
        return {"message": "user has rated the game"}
    else:
        return {"message": "user has not rated the game"}