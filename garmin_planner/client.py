import garth
from garth.exc import GarthException
from garmin_planner.__init__ import logger

SESSION_DIR = '.garth'

class Client(object):
    def __init__(self, email, password):
        self._email = email
        self._password = password

        if not self.login():
            raise Exception("Login failed")
     
    def getAllWorkouts(self) -> dict:
        return garth.connectapi(f"""/workout-service/workouts""",
                                params={"start": 1, "limit": 999, "myWorkoutsOnly": True, "sharedWorkoutsOnly": False, "orderBy": "WORKOUT_NAME", "orderSeq": "ASC", "includeAtp": False})

    def deleteWorkout(self, workout: dict) -> bool:
        res = garth.connectapi(f"""/workout-service/workout/{workout['workoutId']}""",
                               method="DELETE")
        if res != None:
            logger.info(f"""Deleted workoutId: {workout['workoutId']} workoutName: {workout['workoutName']}""")
            return True
        else:
            logger.warn(f"""Could not delete workout. Workout not found with workoutId: {workout['workoutId']} (workoutName: {workout['workoutName']})""")
            return False

    def scheduleWorkout(self, id, dateJson: dict) -> bool:
        resJson = garth.connectapi(f"""/workout-service/schedule/{id}""",
                               method="POST",
                               headers={'Content-Type': 'application/json'},
                               json=dateJson)
        if ('workoutScheduleId' not in resJson):
            return False
        return True

    def importWorkout(self, workoutJson) -> dict:
        resJson = garth.connectapi(f"""/workout-service/workout""",
                               method="POST",
                               headers={'Content-Type': 'application/json'},
                               data=workoutJson)
        logger.info(f"""Imported workout {resJson['workoutName']}""")
        return resJson

    def getActivities(self, limit: int = 10) -> list:
        """Fetch recent activities from Garmin Connect."""
        try:
            # Try GET first
            result = garth.connectapi(f"""/activitylist-service/activities/search/activities""",
                                      params={"start": 0, "limit": limit})
            if isinstance(result, list):
                return result
            return result.get('activities', []) if isinstance(result, dict) else []
        except Exception as e:
            logger.warning(f"Failed to fetch activities with GET, trying alternative: {e}")
            try:
                # Fallback: try POST
                result = garth.connectapi(f"""/activity-service/activities/search/activities""",
                                         method="POST",
                                         json={"startIndexInResults": 0, "maxResults": limit})
                return result if isinstance(result, list) else result.get('activities', [])
            except Exception as e2:
                logger.error(f"Both activity fetch methods failed: {e2}")
                return []

    def getActivitySplits(self, activityId: int) -> dict:
        """Fetch typed splits for a specific activity."""
        return garth.connectapi(f"""/activity-service/activity/{activityId}/typedsplits""")
    
    def login(self) -> bool:
        try:
            garth.resume(SESSION_DIR)
            garth.client.username
        except (FileNotFoundError, GarthException):
            garth.login(self._email, self._password)
            garth.save(SESSION_DIR)
        return True