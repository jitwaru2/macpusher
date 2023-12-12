import os
import pushbullet


def handle(domain, app, title, body):
    pb = pushbullet.PushBullet(os.environ.get("PUSHBULLET_API_KEY"))
    push = pb.push_note(
        "[{}] {} | {}".format(domain, app, title), 
        body,
    )
