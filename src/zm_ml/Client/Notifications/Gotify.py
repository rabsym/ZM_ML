import logging
from typing import Optional

import requests

from ..main import get_global_config
from ...Shared.configs import GlobalConfig

logger = logging.getLogger("ZM_ML-Client")
g: Optional[GlobalConfig] = None


class Gotify:
    def __init__(self):
        global g
        g = get_global_config()
        self.noti_cfg = g.config.notifications
        self.config = self.noti_cfg.gotify
        self.title = f"({g.eid}) {g.mon_name}->{g.event_cause}"
        self.message = ''


    def send(self, pred_out: str):
        lp = "gotify::send::"
        url_opts = self.config.url_opts
        _mode = url_opts.mode
        _scale = url_opts.scale
        _max_fps = url_opts.max_fps
        _buffer = url_opts.buffer
        _replay = url_opts.replay
        portal = self.config.portal or g.api.portal_base_url
        host = self.config.host
        token = self.config.token
        link_url = self.config.link_url
        link_user = self.config.link_user
        link_pass = self.config.link_pass

        image_auth = ""
        event_auth = ""
        event_url = ""


        zm_user = g.config.zoneminder.user
        zm_pass = g.config.zoneminder.password
        _link_url = ""
        _embedded_event = ""
        from urllib.parse import urlencode, quote_plus
        if zm_user and zm_pass:
            payload = {'username': zm_user.get_secret_value(), 'password': zm_pass.get_secret_value()}
            image_auth = urlencode(payload, quote_via=quote_plus)
        if link_url:
            if link_user and link_pass:
                payload = {'user': link_user.get_secret_value(), 'pass': link_pass.get_secret_value()}
                event_auth = urlencode(payload, quote_via=quote_plus)
            event_url = (
                f"{portal}/cgi-bin/nph-zms?mode={_mode}&scale="
                f"{_scale}&maxfps={_max_fps}&buffer={_buffer}&replay={_replay}&"
                f"monitor={g.mid}&event={g.eid}&{event_auth}"
            )
            _link_url = f"\n[View event in browser]({event_url})"
            # _embedded_event = f"![Embedded event video]({event_url})"
        try:
            
            # goti_image_url: str = f"{g.api.portal_url}/index.php?view=image&eid={g.eid}&fid=objdetect&{push_zm_tkn}"
            image_url: str = (
                f"{portal}/index.php?view=image&eid={g.eid}&fid="
                f"objdetect&{image_auth}"
            )
            logger.debug(f"{image_url = } -- | -- {event_url = }")
            test_ = "https://placekitten.com/400/200"
            markdown_formatted_msg: str = (
                f"{pred_out}\n{_link_url}"
                f"![detection.jpeg]({image_url})\n"
                f"{_embedded_event}"
            )
            # \n![Embedded event video for gotify web app]({goti_event_url})

            data = {
                "title": self.title,
                "message": markdown_formatted_msg,
                "priority": 100,
                "extras": {
                    "client::display": {"contentType": "text/markdown"},
                    "client::notification": {
                        "bigImageUrl": f"{image_url}",
                        # "click": {
                        #     "url": f"{goti_event_url}",
                        # },
                    },
                },
            }
            resp = requests.post(
                f"{host}/message?token={token}", json=data
            )
        except Exception as custom_push_exc:
            logger.error(
                f"{lp} ERROR while sending Gotify notification "
            )
            logger.debug(f"{lp} EXCEPTION>>> {custom_push_exc}")
        else:
            # g.logger.debug(f"{lp} response from gotify -> {resp.status_code=} - {resp.text = }")
            if resp and resp.status_code == 200:
                logger.debug(f"{lp} Gotify returned SUCCESS")
            elif resp and resp.status_code != 200:
                logger.debug(
                    f"{lp} Gotify FAILURE STATUS_CODE: {resp.status_code} -> {resp.json()}"
                )