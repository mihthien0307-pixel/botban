from app.login.client import *
from app.helpers.methods import *
from app.module.commandLoader import *
from app.helpers.message import *
from src.command.antimanager.index import handleListenAnti
from src.services.utils.im_core import DontcareMessage
from src.services.utils.lazy_undo import handle_reaction_undo, push_bot_message
from src.services.init.index import *
from app.module.message import *
from src.command.music.timeout import *
from src.command.bot_services.bot_manager.menu import InitTimeoutMenu, MenuReply
from src.command.chat_bot.meme import InitTimeoutMeme
from src.command.chat_bot.truyentranh import InitTimeoutManga
from src.command.bot_services.bot_manager.download import DownloadAutoLink
from src.command.bot_services.bot_manager.verifyShield import handle_verify_join, handle_verify_msg
from src.command.bot_services.bot_manager.autoApprove import _init_auto_approve_loop
from src.command.groupBot.mutegroup import mutegroup_on_event
from src.command.antimanager.antiadd import antiAdd
from src.command.groupBot.ckg import ckgListener
from src.command.groupBot.scold import scoldListener
from src.command.groupBot.tagreaction import tagReactionListener
from api.util.Enum import PermissionLevel, MsgStyle, ThreadType
from api.app.event import GroupEventType

import statistics as _statistics

_LAG_THRESHOLD_MS  = 5000
_LAG_COUNT_TRIGGER = 5
_CHECK_INTERVAL    = 5
_SMOOTH_WINDOW     = 10

def _init_auto_restart_monitor(bot_instance):
    import threading, time, os, sys

    bot_instance._ar_latencies = []
    bot_instance._ar_lag_count = 0
    bot_instance._ar_lock = threading.Lock()

    def _monitor():
        while True:
            time.sleep(_CHECK_INTERVAL)
            try:
                with bot_instance._ar_lock:
                    samples = list(bot_instance._ar_latencies)
                    bot_instance._ar_latencies.clear()

                if not samples:
                    bot_instance._ar_lag_count = 0
                    continue

                avg_ms = _statistics.mean(samples)

                if avg_ms > _LAG_THRESHOLD_MS:
                    bot_instance._ar_lag_count += 1
                    print(f"[AutoRS] ⚠️  Bot {bot_instance.bot} lag avg={avg_ms:.0f}ms ({bot_instance._ar_lag_count}/{_LAG_COUNT_TRIGGER})")
                    if bot_instance._ar_lag_count >= _LAG_COUNT_TRIGGER:
                        print(f"[AutoRS] 🔄 Restart bot {bot_instance.bot} do lag liên tiếp...")
                        bot_instance._ar_lag_count = 0
                        os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                    if bot_instance._ar_lag_count > 0:
                        print(f"[AutoRS] ✅ Bot {bot_instance.bot} mượt trở lại avg={avg_ms:.0f}ms — reset counter")
                    bot_instance._ar_lag_count = 0

            except Exception as _e:
                print(f"[AutoRS] Lỗi monitor: {_e}")

    threading.Thread(target=_monitor, daemon=True, name=f"auto-rs-{bot_instance.bot}").start()


class zrcapis(ZaloAPI, Methods, Utilsmodule, commandHandles, MessageHelper, Listen, MediaCache):

    def __init__(self, api_key, secret_key, imei=None, session_cookies=None,
                 prefix="", is_main_bot=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.audiomackStates:  dict[str, dict] = {}
        self.soundcloudStates: dict[str, dict] = {}
        self.zingStates:       dict[str, dict] = {}
        self.menuStates:       dict[str, dict] = {}
        self.memeStates:       dict[str, object] = {}
        self.mangaStates:      dict[str, object] = {}

        InitTimeoutAudiomack(self)
        InitTimeoutSoundCloud(self)
        InitTimeoutZing(self)
        InitTimeoutMenu(self)
        InitTimeoutMeme(self)
        InitTimeoutManga(self)

        self.is_main_bot     = is_main_bot
        self.commands        = loader(self, "src/command")
        self.prefix          = prefix
        self.imei            = imei
        self.session_cookies = session_cookies
        self.secret_key      = secret_key
        self.api_key         = api_key
        self.bot             = self.fetchAccountInfo().profile.displayName
        self.msgUser:        dict[str, str] = {}
        self._botMessages:   dict[str, dict] = {}

        initAdmin(self)
        doneRestart(self)
        clearpyc(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        _init_auto_approve_loop(self)
        _init_auto_restart_monitor(self)

    def send(self, message, threadId, type=ThreadType.USER, mark_message=None, ttl=0):
        sent = super().send(message, threadId, type, mark_message, ttl)
        push_bot_message(self, sent, threadId)
        return sent

    def replyMessageStyle(self, message, replyMsg, threadId, threadType, ttl=0,
                          color=None, title=None, mention=None, userId=None):
        sent = super().replyMessageStyle(message, replyMsg, threadId, threadType, ttl,
                                         color, title, mention, userId)
        push_bot_message(self, sent, threadId)
        return sent

    def onEvent(self, EventData, EventType):
        from src.events.zaloEvent import ZaloEventHandle
        try:
            ZaloEventHandle(self, EventData, EventType)
            mutegroup_on_event(self, EventData, EventType)
            if EventType == GroupEventType.JOIN:
                handle_verify_join(self, EventData)
        except Exception as e:
            import traceback
            print(f"[ERROR onEvent] {e}\n{traceback.format_exc()}")

    def onMessage(self, mid, userId, message, data, threadId, type):
        _ar_t0 = time.time()
        try:
            if not hasattr(self, "clicc"):
                self.clicc = set()

            cliId = getattr(data, "cliMsgId", None)
            if cliId is not None:
                if cliId in self.clicc:
                    return
                self.clicc.add(cliId)

            name = self.userName(userId)
            msg  = message.text if isinstance(message, Message) else str(message)

            if getattr(data, "msgType", None) == "chat.recommended":
                message = (getattr(data.content, "title", "") or "") + " "

            self.msgUser[name] = message

            # MenuReply chạy sớm nhất — tin nhắn "Trả lời" (quote) có cấu trúc
            # data khác thường, nếu để sau các listener khác thì một lỗi ở
            # listener nào đó (ví dụ parse data.reference) sẽ chặn luôn MenuReply.
            try:
                MenuReply(self, message, data, userId, threadId, type)
            except Exception as e:
                import traceback
                print(f"[ERROR MenuReply] {e}\n{traceback.format_exc()}")

            try:
                forward = data.reference and json.loads(data.reference["data"]).get("fwLvl")
            except Exception:
                forward = None

            handleListenAnti(self, message, data, userId, threadId, type)
            ckgListener(self, message, data, userId, threadId, type)
            scoldListener(self, message, data, userId, threadId, type)
            tagReactionListener(self, message, data, userId, threadId, type)
            DontcareMessage(self, message, data, userId, threadId, type)
            handle_reaction_undo(self, message, data, userId, threadId, type)
            handle_verify_msg(self, message, data, userId, threadId, type)

            settings         = read_settings(self.uid)
            allow_group      = settings.get("allowGroup", [])
            high_admins      = settings.get("highAdmin", [])
            bot_admins       = settings.get("adminBot", [])
            developer_admins = settings.get("developerAdmin", [])
            listen_users     = settings.get("listenUsers", [])
            all_admins       = set(high_admins) | set(bot_admins) | set(developer_admins)

            is_admin          = userId in all_admins
            is_allowed_thread = threadId in allow_group
            is_listen_user    = userId in listen_users

            DownloadAutoLink(self, message, data, userId, threadId, type)

            if not is_admin and not is_allowed_thread and not is_listen_user:
                return

            self.loadcommands(message, data, userId, threadId, type)
            self.listenReply(message, data, userId, threadId, type)

            msg_stripped = msg.strip()
            mention = Mention(userId, offset=0, length=len(name))

            if msg_stripped.lower() == "prefix":
                self.replyMessageStyle(
                    f"Prefix của bot {self.bot} hiện tại là: {self.prefix}",
                    data, threadId, type,
                    color="gr", title="SUCCESS", userId=userId,
                )
            elif self.prefix and msg_stripped == self.prefix:
                self.replyMessageStyle(
                    f"Use {self.prefix}menu all to check all commands to use my bot",
                    data, threadId, type,
                    color="gr", title="SUCCESS", userId=userId,
                )

        except Exception as e:
            import traceback
            print(f"[ERROR onMessage] {e}\n{traceback.format_exc()}")
        finally:
            try:
                _ms = (time.time() - _ar_t0) * 1000
                with self._ar_lock:
                    self._ar_latencies.append(_ms)
                    if len(self._ar_latencies) > _SMOOTH_WINDOW:
                        self._ar_latencies = self._ar_latencies[-_SMOOTH_WINDOW:]
            except Exception:
                pass

if __name__ == "__main__":
    main()
