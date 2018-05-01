from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app import db


class ContestClass(db.Model):
    __tablename__ = "contest_classes"

    id = Column(Integer, primary_key=True)
    category = Column(String)
    type = Column(String)
    active_task_gist_url = Column(String)
    contestants_filter_gist_url = Column(String)

    # Relations
    contest_id = Column(Integer, ForeignKey('contests.id', ondelete='SET NULL'))
    contest = relationship('Contest', foreign_keys=[contest_id], backref='classes')

    # Generates a filter file for glidertracker.org
    def gt_filter(self):
        result_list = list()
        result_list.append("ID,CALL,CN,TYPE")
        for contestant in self.contestants:
            parameters = {'live_track_id': contestant.live_track_id,
                          'aircraft_registration': contestant.aircraft_registration,
                          'contestant_number': contestant.contestant_number,
                          'aircraft_model': contestant.aircraft_model}

            entry = '"{live_track_id}","{aircraft_registration}","{contestant_number}","{aircraft_model}"'.format(**parameters)
            result_list.append(entry)

        return "\n".join(result_list)


    def __repr__(self):
        return "<ContestClass %s: %s,%s,%s,%s>" % (
            self.id,
            self.category,
            self.type,
            self.active_task_gist_url,
            self.contestants_filter_gist_url)
