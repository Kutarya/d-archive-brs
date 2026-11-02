import argparse
import gc
import queue
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from animations.effect_registry import create_effect
from cli import send_command
from keyboard_keys import FUNCTION_NAMES, KEY_NAMES, key_label
from managers.errors import MuvvError
from managers.validator import rgb
from profile_io import read_profile_file, write_profile_file
from ui_client import ServiceError, command_then_snapshot, fetch_snapshot, require_ok

try:
    import tkinter as tk
    from tkinter import colorchooser, filedialog, messagebox, simpledialog

    import customtkinter as ctk
except ImportError:
    ctk = None

ACCENT = "#4AD2B1"
BACKGROUND = "#13191F"
PANEL = "#1C242D"
MUTED = "#96A4B2"
EFFECT_NAMES = {"Sabit": "static", "Nefes": "breathing", "Dalga": "wave", "Spektrum": "spectrum"}
BUTTON_NAMES = {
    "Sol tık": "button1",
    "Sağ tık": "button2",
    "Orta tık": "button3",
    "Yan / geri": "button4",
    "Yan / ileri": "button5",
    "DPI": "dpi",
    "Tekerlek yukarı": "scrollup",
    "Tekerlek aşağı": "scrolldown",
}


class MuvvApp:
    def __init__(self, root, client=send_command, demo=False):
        self.root = root
        self.client = client
        self.demo = demo
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="muvv-ui")
        self._results = queue.Queue()
        self._busy = False
        self._closed = False
        self._closed_event = Event()
        self._callbacks = {}
        self._next_job = 0
        self._background = False
        self._pending_job = None
        self._service_online = False
        self._dirty = set()
        self._revisions = {"lighting": 0, "zones": 0, "dpi": 0, "polling": 0}
        self._buttons = []
        self._devices = {}
        self._device_id = None
        self._state = {}
        self._capabilities = {}
        self._preview_effect = None
        self._preview_colors = [(43, 55, 67)] * 3
        self._profile_names = []
        self._profile_records = {}
        self._after_ids = set()
        root.title("Muvv · Demo" if demo else "Muvv")
        root.geometry("1050x760")
        root.minsize(920, 710)
        root.configure(fg_color=BACKGROUND)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._build()
        self._schedule(50, self._poll_results)
        self._schedule(60, self._animate_preview)
        self._schedule(100, self.refresh)
        self._schedule(3000, self._auto_refresh)

    def _schedule(self, delay, callback):
        if not self._closed:

            def run():
                self._after_ids.discard(identifier)
                if not self._closed:
                    callback()

            identifier = self.root.after(delay, run)
            self._after_ids.add(identifier)

    def _button(self, parent, text, command, secondary=False, needs="device", **kwargs):
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=36,
            fg_color="#2B3743" if secondary else ACCENT,
            hover_color="#374756" if secondary else "#37B79A",
            text_color="#E6EDF3" if secondary else "#10241E",
            **kwargs,
        )
        self._buttons.append((button, needs))
        return button

    def _mark_dirty(self, group):
        self._dirty.add(group)
        self._revisions[group] += 1

    def _watch(self, widget, group):
        widget.bind("<KeyRelease>", lambda _: self._mark_dirty(group), add="+")

    def _sync_controls(self):
        transport = self._state.get("transport", {})
        writable = (
            self._service_online
            and self._device_id is not None
            and transport.get("connected", False)
            and not transport.get("state_uncertain")
        )
        for button, needs in self._buttons:
            allowed = {
                "local": True,
                "service": self._service_online,
                "profile": self._service_online and bool(self._profile_names),
                "device": writable,
                "reconnect": self._service_online and self._device_id is not None,
                "effect": writable and self._state.get("effect") is not None,
            }[needs]
            button.configure(
                state="normal" if allowed and (not self._busy or self._background) else "disabled"
            )
        self.device_menu.configure(state="normal" if self._devices and not self._busy else "disabled")
        self.profile_menu.configure(state="normal" if self._profile_names and not self._busy else "disabled")
        if EFFECT_NAMES[self.effect_menu.get()] == "spectrum":
            self.color_picker.configure(state="disabled")

    @staticmethod
    def _label(parent, text, size=13, color="#E6EDF3", **kwargs):
        return ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=size), text_color=color, **kwargs)

    def _build(self):
        sidebar = ctk.CTkFrame(self.root, width=235, corner_radius=0, fg_color=PANEL)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        self._label(sidebar, "MUVV", 32, ACCENT, anchor="w").grid(
            row=0, column=0, padx=24, pady=(27, 0), sticky="ew"
        )
        self._label(sidebar, "Fare kontrolü", color=MUTED, anchor="w").grid(
            row=1, column=0, padx=24, pady=(2, 35), sticky="ew"
        )
        self._label(sidebar, "BAĞLI CİHAZ", 11, MUTED, anchor="w").grid(row=2, column=0, padx=24, sticky="ew")
        self.device_menu = ctk.CTkOptionMenu(
            sidebar, values=["Cihaz bekleniyor"], command=self._select_device, width=190, fg_color="#2B3743"
        )
        self.device_menu.grid(row=3, column=0, padx=22, pady=10, sticky="ew")
        self._button(sidebar, "Cihazları yenile", self.refresh, secondary=True, needs="local").grid(
            row=4, column=0, padx=22, pady=(0, 22), sticky="ew"
        )
        self.device_detail = self._label(
            sidebar, "Servise bağlanılıyor…", color=MUTED, justify="left", wraplength=190, anchor="nw"
        )
        self.device_detail.grid(row=5, column=0, padx=24, sticky="ew")
        sidebar.grid_rowconfigure(6, weight=1)
        if self.demo:
            self._label(
                sidebar, "DEMO\nFareye veri gönderilmez.", 12, ACCENT, justify="left", anchor="w"
            ).grid(row=7, column=0, padx=24, pady=18, sticky="ew")
        self._button(
            sidebar,
            "Cihazı yeniden bağla",
            lambda: self._command("reconnect"),
            secondary=True,
            needs="reconnect",
        ).grid(row=8, column=0, padx=22, pady=8, sticky="ew")
        self._button(sidebar, "Fare belleğine kaydet", self._save_onboard, secondary=True).grid(
            row=9, column=0, padx=22, pady=(0, 24), sticky="ew"
        )

        main = ctk.CTkFrame(self.root, fg_color=BACKGROUND, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew", padx=28, pady=24)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)
        self._label(main, "Cihaz ayarları", 25, anchor="w").grid(row=0, column=0, sticky="ew")
        self._label(
            main, "Işık, hassasiyet ve tuş atamalarını aynı yerden yönetin.", color=MUTED, anchor="w"
        ).grid(row=1, column=0, pady=(4, 18), sticky="ew")
        self.tabs = ctk.CTkTabview(
            main,
            fg_color=PANEL,
            segmented_button_selected_color="#2F6B5E",
            segmented_button_selected_hover_color="#367E6C",
        )
        self.tabs.grid(row=2, column=0, sticky="nsew")
        pages = {}
        for name in ("Aydınlatma", "DPI ve hız", "Tuşlar", "Profiller"):
            tab = self.tabs.add(name)
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)
            pages[name] = ctk.CTkScrollableFrame(tab, fg_color=PANEL, corner_radius=0)
            pages[name].grid(row=0, column=0, sticky="nsew")
            pages[name].grid_columnconfigure(0, weight=1)
        self._pages = pages
        self._lighting(pages["Aydınlatma"])
        self._dpi(pages["DPI ve hız"])
        self._keys(pages["Tuşlar"])
        self._profiles(pages["Profiller"])
        self.status_label = self._label(
            main, "Hazırlanıyor…", color=MUTED, anchor="w", wraplength=690, justify="left"
        )
        self.status_label.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        self._sync_controls()

    def _lighting(self, tab):
        self._label(tab, "RGB efekti", 19, anchor="w").grid(
            row=0, column=0, padx=22, pady=(18, 0), sticky="ew"
        )
        self.preview = tk.Canvas(tab, height=128, bg=PANEL, highlightthickness=0)
        self.preview.grid(row=1, column=0, padx=22, pady=12, sticky="ew")
        self._preview_items = []
        self._preview_labels = []
        for index, name in enumerate(("Tekerlek", "Orta", "Alt")):
            x = 92 + index * 190
            item = self.preview.create_rectangle(x - 45, 20, x + 45, 79, fill="#4AD2B1", outline="")
            label = self.preview.create_text(x, 104, text=name, fill=MUTED, font=("Segoe UI", 11))
            self._preview_items.append(item)
            self._preview_labels.append(label)
        self.preview.bind("<Configure>", self._resize_preview)
        fields = ctk.CTkFrame(tab, fg_color="transparent")
        fields.grid(row=2, column=0, padx=22, sticky="ew")
        fields.grid_columnconfigure(1, weight=1)
        self._label(fields, "Efekt").grid(row=0, column=0, sticky="w", pady=9)
        self.effect_menu = ctk.CTkOptionMenu(fields, values=list(EFFECT_NAMES), command=self._effect_changed)
        self.effect_menu.grid(row=0, column=1, padx=(20, 0), sticky="ew")
        self._label(fields, "Renk").grid(row=1, column=0, sticky="w", pady=9)
        color_frame = ctk.CTkFrame(fields, fg_color="transparent")
        color_frame.grid(row=1, column=1, padx=(20, 0), sticky="ew")
        self.color_entry = ctk.CTkEntry(color_frame, width=150)
        self.color_entry.insert(0, "#4AD2B1")
        self._watch(self.color_entry, "lighting")
        self.color_entry.pack(side="left")
        self.color_picker = self._button(
            color_frame, "Renk seç", self._choose_color, secondary=True, needs="local", width=100
        )
        self.color_picker.pack(side="left", padx=10)
        self._label(fields, "Hız").grid(row=2, column=0, sticky="w", pady=9)
        self.speed = ctk.CTkSlider(
            fields, from_=0, to=20, number_of_steps=400, command=lambda _: self._mark_dirty("lighting")
        )
        self.speed.set(1)
        self.speed.grid(row=2, column=1, padx=(20, 0), sticky="ew")
        self._label(fields, "Dalga yönü").grid(row=3, column=0, sticky="w", pady=9)
        self.direction = ctk.CTkOptionMenu(
            fields, values=["Dikey", "Yatay"], command=lambda _: self._mark_dirty("lighting")
        )
        self.direction.grid(row=3, column=1, padx=(20, 0), sticky="ew")
        self._label(fields, "Dalga boyu").grid(row=4, column=0, sticky="w", pady=9)
        self.wave_length = ctk.CTkEntry(fields)
        self.wave_length.insert(0, "0.5")
        self._watch(self.wave_length, "lighting")
        self.wave_length.grid(row=4, column=1, padx=(20, 0), sticky="ew")
        self._label(fields, "Spektrum parlaklığı").grid(row=5, column=0, sticky="w", pady=9)
        self.brightness = ctk.CTkSlider(
            fields, from_=0, to=1, number_of_steps=100, command=lambda _: self._mark_dirty("lighting")
        )
        self.brightness.set(1)
        self.brightness.grid(row=5, column=1, padx=(20, 0), sticky="ew")
        actions = ctk.CTkFrame(tab, fg_color="transparent")
        actions.grid(row=3, column=0, padx=22, pady=(22, 12), sticky="ew")
        self._button(actions, "Efekti uygula", self._apply_effect).pack(side="left")
        self._button(actions, "Efekti güncelle", self._update_effect, secondary=True, needs="effect").pack(
            side="left", padx=12
        )
        self._button(
            tab,
            "Animasyonu durdur · rengi koru",
            lambda: self._command("stop-effect"),
            secondary=True,
            needs="effect",
        ).grid(row=4, column=0, padx=22, pady=8, sticky="w")
        self._label(tab, "Bölgelere ayrı renk ver", 19, anchor="w").grid(
            row=5, column=0, padx=22, pady=(20, 10), sticky="ew"
        )
        zones = ctk.CTkFrame(tab, fg_color="transparent")
        zones.grid(row=6, column=0, padx=22, sticky="ew")
        self.zone_entries = {}
        for index, (zone, label) in enumerate(
            (("wheel", "Tekerlek"), ("middle", "Orta"), ("underglow", "Alt"))
        ):
            zones.grid_columnconfigure(index, weight=1)
            self._label(zones, label, color=MUTED).grid(row=0, column=index, pady=(0, 6))
            entry = ctk.CTkEntry(zones, width=110, justify="center")
            entry.insert(0, "#4AD2B1")
            entry.grid(row=1, column=index, padx=5, sticky="ew")
            self._watch(entry, "zones")
            self.zone_entries[zone] = entry
        self._button(tab, "Üç bölgeyi uygula", self._apply_colors).grid(
            row=7, column=0, padx=22, pady=(16, 22), sticky="w"
        )
        self._effect_changed()

    def _dpi(self, tab):
        self._label(tab, "DPI kademeleri", 19, anchor="w").grid(
            row=0, column=0, padx=22, pady=(22, 8), sticky="ew"
        )
        self.dpi_note = self._label(
            tab,
            "Faredeki değerler okunamaz. Bu alanlar önerilen başlangıç değerleridir.",
            color=MUTED,
            anchor="w",
            wraplength=640,
            justify="left",
        )
        self.dpi_note.grid(row=1, column=0, padx=22, sticky="ew")
        stages = ctk.CTkFrame(tab, fg_color="transparent")
        stages.grid(row=2, column=0, padx=22, pady=25, sticky="ew")
        self.dpi_entries = []
        for index, value in enumerate((400, 800, 1200, 2400, 3200)):
            stages.grid_columnconfigure(index, weight=1)
            self._label(stages, f"Kademe {index + 1}", color=MUTED).grid(row=0, column=index, pady=(0, 8))
            entry = ctk.CTkEntry(stages, width=96, justify="center")
            entry.insert(0, str(value))
            self._watch(entry, "dpi")
            entry.grid(row=1, column=index, padx=5, sticky="ew")
            self.dpi_entries.append(entry)
        active = ctk.CTkFrame(tab, fg_color="transparent")
        active.grid(row=3, column=0, padx=22, sticky="ew")
        self._label(active, "Etkin kademe").pack(side="left")
        self.active_stage = ctk.CTkOptionMenu(
            active, values=["1", "2", "3", "4", "5"], width=95, command=lambda _: self._mark_dirty("dpi")
        )
        self.active_stage.pack(side="left", padx=20)
        self._button(active, "Beş kademeyi uygula", self._apply_dpi).pack(side="right")
        self.dpi_range = self._label(
            tab, "Rival 3 Gen 2: 200–8500 DPI, 100 DPI adımlarla.", color=MUTED, anchor="w"
        )
        self.dpi_range.grid(row=4, column=0, padx=22, pady=(15, 30), sticky="ew")
        self._label(tab, "Yoklama hızı", 19, anchor="w").grid(row=5, column=0, padx=22, sticky="ew")
        polling = ctk.CTkFrame(tab, fg_color="transparent")
        polling.grid(row=6, column=0, padx=22, pady=18, sticky="ew")
        self.polling_menu = ctk.CTkOptionMenu(
            polling,
            values=["Bilinmiyor", "125", "250", "500", "1000"],
            command=lambda _: self._mark_dirty("polling"),
        )
        self.polling_menu.pack(side="left")
        self._button(polling, "Hızı uygula", self._apply_polling).pack(side="right")

    def _keys(self, tab):
        self._label(tab, "Tuş atama", 19, anchor="w").grid(
            row=0, column=0, padx=22, pady=(22, 10), sticky="ew"
        )
        self._label(
            tab,
            "Bir klavye tuşu veya fare işlevi seçin. En az bir sol tık ataması korunur.",
            color=MUTED,
            wraplength=640,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, padx=22, sticky="ew")
        fields = ctk.CTkFrame(tab, fg_color="transparent")
        fields.grid(row=2, column=0, padx=22, pady=18, sticky="ew")
        fields.grid_columnconfigure(1, weight=1)
        self._label(fields, "Fare tuşu").grid(row=0, column=0, sticky="w", pady=8)
        self.button_menu = ctk.CTkOptionMenu(fields, values=list(BUTTON_NAMES))
        self.button_menu.set("Yan / geri")
        self.button_menu.grid(row=0, column=1, padx=(18, 0), sticky="ew")
        self._label(fields, "Atama türü").grid(row=1, column=0, sticky="w", pady=8)
        self.assignment_menu = ctk.CTkOptionMenu(
            fields, values=["Klavye tuşu", "Fare işlevi"], command=self._assignment_changed
        )
        self.assignment_menu.grid(row=1, column=1, padx=(18, 0), sticky="ew")
        self._label(fields, "Klavye tuşu").grid(row=2, column=0, sticky="w", pady=8)
        self.key_menu = ctk.CTkOptionMenu(fields, values=list(KEY_NAMES), command=self._pick_key)
        self.key_menu.grid(row=2, column=1, padx=(18, 0), sticky="ew")
        self.usage_label = self._label(fields, "HID kodu")
        self.usage_label.grid(row=3, column=0, sticky="w", pady=8)
        self.usage_entry = ctk.CTkEntry(fields, width=130, placeholder_text="0x04")
        self.usage_entry.insert(0, "0x04")
        self.usage_entry.grid(row=3, column=1, padx=(18, 0), sticky="ew")
        self._label(fields, "Fare işlevi").grid(row=4, column=0, sticky="w", pady=8)
        self.function_menu = ctk.CTkOptionMenu(fields, values=list(FUNCTION_NAMES))
        self.function_menu.set("Geri")
        self.function_menu.grid(row=4, column=1, padx=(18, 0), sticky="ew")
        self.advanced_keys = ctk.CTkCheckBox(
            fields, text="Gelişmiş tuş kodunu göster", command=self._toggle_usage
        )
        self.advanced_keys.grid(row=5, column=1, padx=(18, 0), pady=(10, 0), sticky="w")
        self._toggle_usage()
        self._assignment_changed()
        self.initialize_buttons = ctk.CTkCheckBox(tab, text="Bilinmeyen tuş düzenini varsayılanlarla başlat")
        self.initialize_buttons.grid(row=3, column=0, padx=22, pady=(0, 13), sticky="w")
        self.persist_buttons = ctk.CTkCheckBox(tab, text="Atamayı fare belleğine de kaydet")
        self.persist_buttons.grid(row=4, column=0, padx=22, sticky="w")
        actions = ctk.CTkFrame(tab, fg_color="transparent")
        actions.grid(row=5, column=0, padx=22, pady=22, sticky="ew")
        self._button(actions, "Tuşu ata", self._bind).pack(side="left")
        self._button(actions, "Varsayılan tuşları yükle", self._restore_buttons, secondary=True).pack(
            side="left", padx=12
        )
        self.button_state = ctk.CTkTextbox(tab, height=185, fg_color=BACKGROUND)
        self.button_state.grid(row=6, column=0, padx=22, pady=(0, 12), sticky="ew")

    def _profiles(self, tab):
        self._label(tab, "Bilgisayardaki profiller", 19, anchor="w").grid(
            row=0, column=0, padx=22, pady=(22, 10), sticky="ew"
        )
        self._label(
            tab,
            "Profil yalnızca bu oturumda bilinen ayarları içerir; fareden alınmış bir yedek değildir.",
            color=MUTED,
            wraplength=640,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, padx=22, sticky="ew")
        save = ctk.CTkFrame(tab, fg_color="transparent")
        save.grid(row=2, column=0, padx=22, pady=22, sticky="ew")
        self.profile_name = ctk.CTkEntry(save, placeholder_text="Profil adı", width=260)
        self.profile_name.pack(side="left")
        self._button(save, "Yeni profil kaydet", self._save_profile).pack(side="right")
        self.profile_menu = ctk.CTkOptionMenu(tab, values=["Profil seç"], command=self._show_profile)
        self.profile_menu.grid(row=3, column=0, padx=22, sticky="ew")
        self.persist_profile = ctk.CTkCheckBox(tab, text="Uyguladıktan sonra fare belleğine kaydet")
        self.persist_profile.grid(row=4, column=0, padx=22, pady=20, sticky="w")
        actions = ctk.CTkFrame(tab, fg_color="transparent")
        actions.grid(row=5, column=0, padx=22, sticky="ew")
        self._button(actions, "Profili uygula", self._apply_profile).pack(side="left")
        self._button(actions, "Adını değiştir", self._rename_profile, secondary=True, needs="profile").pack(
            side="left", padx=12
        )
        self._button(actions, "Sil", self._delete_profile, secondary=True, needs="profile", width=65).pack(
            side="left"
        )
        self.profile_detail = ctk.CTkTextbox(tab, height=195, fg_color=BACKGROUND)
        self.profile_detail.grid(row=6, column=0, padx=22, pady=20, sticky="ew")
        exchange = ctk.CTkFrame(tab, fg_color="transparent")
        exchange.grid(row=7, column=0, padx=22, sticky="ew")
        self._button(exchange, "JSON içe aktar", self._import_profile, secondary=True, needs="service").pack(
            side="left"
        )
        self._button(exchange, "JSON dışa aktar", self._export_profile, secondary=True, needs="profile").pack(
            side="left", padx=12
        )
        self.profile_issues = self._label(
            tab, "", color="#FFAD9C", anchor="w", justify="left", wraplength=620
        )
        self.profile_issues.grid(row=8, column=0, padx=22, pady=(15, 22), sticky="ew")

    def _status(self, message, error=False):
        self.status_label.configure(text=message, text_color="#FFAD9C" if error else MUTED)

    def _submit(self, task, callback, background=False):
        if self._closed:
            return
        if self._busy:
            # A read-only background refresh may delay one explicit action, never lose it.
            if self._background and not background and self._pending_job is None:
                self._pending_job = (task, callback)
                self._status("Cihaz bilgileri yenileniyor; işleminiz sırada.")
                self._sync_controls()
            return
        # Tk resources must be reclaimed on the UI thread, including across successive windows.
        gc.collect()
        self._busy, self._background = True, background
        self._next_job += 1
        token = self._next_job
        self._callbacks[token] = callback
        self._sync_controls()
        if not background:
            self._status("İşlem sürüyor…")
        future = self._executor.submit(task)
        results, closed = self._results, self._closed_event

        def completed(result):
            # Do not retain a Tk widget or UI callback in an I/O thread after the window closes.
            if not closed.is_set():
                results.put((token, result))

        future.add_done_callback(completed)

    def _poll_results(self):
        if self._closed:
            return
        try:
            token, future = self._results.get_nowait()
        except queue.Empty:
            pass
        else:
            self._busy, self._background = False, False
            callback = self._callbacks.pop(token)
            try:
                callback(future.result())
            except Exception as error:
                self._io_error(error)
            pending, self._pending_job = self._pending_job, None
            self._sync_controls()
            if pending is not None:
                self._submit(*pending)
        self._schedule(50, self._poll_results)

    def _io_error(self, error):
        code = error.code if isinstance(error, (ServiceError, MuvvError)) else ""
        if code in ("connection_error", "invalid_request"):
            self._service_online = False
            self.device_detail.configure(text="Servise ulaşılamıyor.\nLinux'ta muvvd servisini başlatın.")
        if code in ("operation_uncertain", "transport_error"):
            self._state.setdefault("transport", {}).update(connected=False, state_uncertain=True)
        self._status(str(error), error=True)

    def _auto_refresh(self):
        if not self._busy:
            self.refresh(background=True)
        self._schedule(3000, self._auto_refresh)

    def refresh(self, background=False, selected=None):
        client = self.client
        identity = self._device_id if selected is None else selected
        self._submit(
            lambda: fetch_snapshot(client, identity),
            lambda result: self._refreshed(result, background=background),
            background=background,
        )

    def _refreshed(self, result, background=False):
        devices, profiles = result["devices"], result["profiles"]
        selected, info = result["selected_device"], result["info"]
        changed = selected != self._device_id
        was_online = self._service_online
        self._service_online = True
        if changed:
            self._dirty.clear()
        self._devices = {
            f"{device['index']} · {device['name'].removeprefix('SteelSeries ')}": device["id"]
            for device in devices
        }
        self._device_id = selected
        labels = list(self._devices) or ["Cihaz bağlı değil"]
        self.device_menu.configure(values=labels)
        self.device_menu.set(
            next((label for label, identity in self._devices.items() if identity == selected), labels[0])
        )
        self._profile_names = [profile["name"] for profile in profiles]
        names = self._profile_names or ["Profil seç"]
        previous = self.profile_menu.get()
        self.profile_menu.configure(values=names)
        if previous not in names:
            self.profile_menu.set(names[0])
            self._text(
                self.profile_detail,
                "Bir profil seçerek ayrıntılarını görüntüleyin." if profiles else "Kayıtlı profil yok.",
            )
        issues = result.get("profile_errors", [])
        notes = [f"{len(issues)} profil okunamadı. Sağlam profilleri kullanabilirsiniz."] if issues else []
        notes.extend(f"{issue['file']}: {issue['message']}" for issue in issues[:2])
        if result.get("profile_limit_exceeded"):
            notes.append("Profil klasörü sınırı aşıldı (128 profil). Klasörü kontrol edin.")
        self.profile_issues.configure(text="\n".join(notes))
        if info is None:
            self._load_info({})
            self.device_detail.configure(
                text="Desteklenen fare bulunamadı." if not selected else "Cihaz meşgul; bilgileri bekleniyor."
            )
        else:
            self._load_info(info)
        if not background or changed or not was_online:
            self._status(
                "Demo hazır. Fareye veri gönderilmez."
                if self.demo
                else ("Cihaz ayarları güncel." if info else "Desteklenen fareyi bağlayın.")
            )
        if result.get("device_error"):
            self._status(result["device_error"]["message"], error=True)
        self._sync_controls()

    def _select_device(self, label):
        if self._busy:
            self.device_menu.set(
                next((name for name, identity in self._devices.items() if identity == self._device_id), label)
            )
            return
        if self._dirty and not messagebox.askyesno(
            "Cihazı değiştir",
            "Uygulanmamış girişler var. Cihazı değiştirirken bu girişler sıfırlansın mı?",
            parent=self.root,
        ):
            self.device_menu.set(
                next(name for name, identity in self._devices.items() if identity == self._device_id)
            )
            return
        self.refresh(selected=self._devices.get(label))

    def _load_info(self, info):
        self._capabilities = info.get("capabilities", {})
        self._state = info.get("state", {})
        settings = self._state.get("settings", {})
        transport = self._state.get("transport", {})
        self.device_detail.configure(
            text="Rival 3 Gen 2 · USB\n3 RGB bölgesi\n\n"
            + (
                "Ayarlar belirsiz; yeniden bağlayın."
                if transport.get("state_uncertain")
                else "Bağlantı hazır."
            )
        )
        dpi = settings.get("dpi")
        if "dpi" not in self._dirty:
            values = dpi["stages"] if dpi else [400, 800, 1200, 2400, 3200]
            for entry, value in zip(self.dpi_entries, values, strict=True):
                self._replace_entry(entry, str(value))
            self.active_stage.set(str(dpi["active"] + 1) if dpi else "1")
        if "polling" not in self._dirty:
            self.polling_menu.set(str(settings.get("polling_rate", "Bilinmiyor")))
        self.dpi_note.configure(
            text="Uygulanmamış girişler korunuyor."
            if "dpi" in self._dirty
            else (
                "Bu oturumda uygulanan beş DPI kademesi."
                if dpi
                else "Faredeki değerler okunamaz. Alanlarda önerilen başlangıç değerleri var."
            )
        )
        buttons = settings.get("buttons")
        text = (
            "\n".join(
                f"{name}: {self._button_label(buttons[identifier])}"
                for name, identifier in BUTTON_NAMES.items()
            )
            if buttons
            else "Tuş atamaları okunmadı.\nİlk değişiklik için tam düzen veya açıkça varsayılan başlangıç gerekir."
        )
        self._text(self.button_state, text)
        effect = self._state.get("effect")
        colors = settings.get("colors", {})
        self._preview_colors = [colors.get(zone, [43, 55, 67]) for zone in self.zone_entries]
        if effect and (
            self._preview_effect is None
            or self._preview_effect.EFFECT_ID != effect["name"]
            or self._preview_effect.parameters() != effect["options"]
        ):
            self._preview_effect = create_effect(effect["name"], effect["options"])
        elif not effect:
            self._preview_effect = None
        if "zones" not in self._dirty:
            for zone, entry in self.zone_entries.items():
                self._replace_entry(entry, self._hex(colors.get(zone, [74, 210, 177])))
        if "lighting" in self._dirty:
            return
        if effect:
            self.effect_menu.set(
                next(
                    (name for name, identifier in EFFECT_NAMES.items() if identifier == effect["name"]),
                    "Sabit",
                )
            )
            options = effect["options"]
        else:
            self.effect_menu.set("Sabit")
            options = {}
        self._replace_entry(self.color_entry, self._hex(options.get("color", [74, 210, 177])))
        self.speed.set(options.get("speed", 1))
        self.brightness.set(options.get("brightness", 1))
        self.direction.set("Yatay" if options.get("direction") == "horizontal" else "Dikey")
        self._replace_entry(self.wave_length, str(options.get("wave_length", 0.5)))
        self._effect_changed()

    @staticmethod
    def _replace_entry(entry, value):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value)

    @staticmethod
    def _hex(color):
        return "#" + "".join(f"{channel:02X}" for channel in color)

    @staticmethod
    def _text(widget, value):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    @staticmethod
    def _button_label(value):
        if isinstance(value, (tuple, list)):
            return f"Klavye: {key_label(value[1])} (0x{value[1]:02X})"
        return next((name for name, code in FUNCTION_NAMES.items() if code == value), str(value))

    def _command(self, command, args=None, device=True):
        if device and self._device_id is None:
            self._status("Önce bağlı bir cihaz seçin.", error=True)
            return
        selected = self._device_id
        payload = {**({"device": selected} if device else {}), **(args or {})}
        client = self.client
        groups = {
            "set-effect": ("lighting",),
            "update-effect": ("lighting",),
            "set-colors": ("zones",),
            "set-dpi-stages": ("dpi",),
            "set-polling": ("polling",),
            "apply-profile": ("lighting", "zones", "dpi", "polling"),
            "reconnect": ("lighting", "zones", "dpi", "polling"),
        }.get(command, ())
        revisions = {group: self._revisions[group] for group in groups}

        def done(result):
            response = result["response"]
            for group, revision in revisions.items():
                if self._revisions[group] == revision:
                    self._dirty.discard(group)
            if result["snapshot"] is not None:
                self._refreshed(result["snapshot"])
            message = "Ayar uygulandı; fareden geri okuma desteklenmiyor."
            if response.get("persistence_requested"):
                message = "Ayar uygulandı ve fareye kaydetme komutu gönderildi."
            messages = {
                "save-profile": "Profil bilgisayara kaydedildi.",
                "import-profile": "Profil bilgisayara alındı. Cihaza uygulamak için profili seçin.",
                "rename-profile": "Profilin adı değiştirildi.",
                "delete-profile": "Profil silindi.",
                "reconnect": "Cihaz yeniden bağlandı. Önceki ayarlar artık bilinmiyor.",
                "stop-effect": "Animasyon durduruldu. Son renkler korundu.",
            }
            message = messages.get(command, message)
            if command in ("save-profile", "import-profile", "rename-profile", "delete-profile"):
                self._profile_records.clear()
                self._text(self.profile_detail, "Profili seçerek güncel ayrıntılarını görüntüleyin.")
            if result["refresh_error"]:
                message += " Bilgiler yenilenemedi: " + result["refresh_error"]
                self._service_online = False
            self._status(message)

        self._submit(lambda: command_then_snapshot(client, command, payload, selected), done)

    def _effect_changed(self, *selection):
        if selection:
            self._mark_dirty("lighting")
        effect = EFFECT_NAMES[self.effect_menu.get()]
        self.color_entry.configure(state="normal" if effect != "spectrum" else "disabled")
        self.speed.configure(state="normal" if effect != "static" else "disabled")
        self.direction.configure(state="normal" if effect == "wave" else "disabled")
        self.wave_length.configure(state="normal" if effect == "wave" else "disabled")
        self.brightness.configure(state="normal" if effect == "spectrum" else "disabled")
        if hasattr(self, "profile_menu"):
            self._sync_controls()

    def _effect_options(self):
        effect = EFFECT_NAMES[self.effect_menu.get()]
        options = {}
        if effect != "spectrum":
            options["color"] = list(rgb(self.color_entry.get()))
        if effect != "static":
            options["speed"] = self.speed.get()
        if effect == "wave":
            options.update(
                direction="vertical" if self.direction.get() == "Dikey" else "horizontal",
                wave_length=float(self.wave_length.get()),
            )
        if effect == "spectrum":
            options["brightness"] = self.brightness.get()
        create_effect(effect, options)
        return effect, options

    def _apply_effect(self):
        try:
            effect, options = self._effect_options()
            self._command("set-effect", {"effect": effect, **options})
        except (MuvvError, ValueError) as error:
            self._status(str(error), error=True)

    def _update_effect(self):
        try:
            effect, options = self._effect_options()
            current = self._state.get("effect")
            if not current or current["name"] != effect:
                raise ValueError("Seçtiğiniz efekti önce uygulayın.")
            self._command("update-effect", options)
        except (MuvvError, ValueError) as error:
            self._status(str(error), error=True)

    def _choose_color(self):
        try:
            initial = self._hex(rgb(self.color_entry.get()))
        except MuvvError:
            initial = ACCENT
        color = colorchooser.askcolor(parent=self.root, initialcolor=initial, title="RGB rengi")[1]
        if color:
            self.color_entry.delete(0, "end")
            self.color_entry.insert(0, color.upper())
            self._mark_dirty("lighting")

    def _apply_colors(self):
        try:
            colors = {zone: list(rgb(entry.get())) for zone, entry in self.zone_entries.items()}
            self._command("set-colors", {"colors": colors})
        except MuvvError as error:
            self._status(str(error), error=True)

    def _resize_preview(self, event):
        spacing = event.width / 3
        half = min(45, spacing / 3)
        for index, (item, label) in enumerate(zip(self._preview_items, self._preview_labels, strict=True)):
            center = spacing * (index + 0.5)
            self.preview.coords(item, center - half, 20, center + half, 79)
            self.preview.coords(label, center, 104)

    def _animate_preview(self):
        if self._closed:
            return
        if self._preview_effect:
            colors = self._preview_effect.apply(3, [(0.5, 0.1), (0.5, 0.5), (0.5, 0.9)])
        else:
            colors = self._preview_colors
        for item, color in zip(self._preview_items, colors, strict=True):
            self.preview.itemconfigure(item, fill="#" + "".join(f"{channel:02X}" for channel in color))
        self._schedule(60, self._animate_preview)

    def _apply_dpi(self):
        try:
            stages = [int(entry.get()) for entry in self.dpi_entries]
            self._command("set-dpi-stages", {"stages": stages, "active": int(self.active_stage.get()) - 1})
        except ValueError:
            self._status("DPI değerleri tam sayı olmalı.", error=True)

    def _apply_polling(self):
        try:
            self._command("set-polling", {"hz": int(self.polling_menu.get())})
        except ValueError:
            self._status("Bir yoklama hızı seçin.", error=True)

    def _bind(self):
        try:
            if self.assignment_menu.get() == "Fare işlevi":
                self._command(
                    "set-button",
                    {
                        "button": BUTTON_NAMES[self.button_menu.get()],
                        "assignment": FUNCTION_NAMES[self.function_menu.get()],
                        "initialize": bool(self.initialize_buttons.get()),
                        "persist": bool(self.persist_buttons.get()),
                    },
                )
                return
            value = self.usage_entry.get()
            usage = int(value, 16 if value.lower().startswith("0x") else 10)
            self._command(
                "bind-key",
                {
                    "button": BUTTON_NAMES[self.button_menu.get()],
                    "key_code": usage,
                    "initialize": bool(self.initialize_buttons.get()),
                    "persist": bool(self.persist_buttons.get()),
                },
            )
        except ValueError:
            self._status("Geçerli bir HID tuş kodu girin.", error=True)

    def _assignment_changed(self, *_):
        keyboard = self.assignment_menu.get() == "Klavye tuşu"
        self.key_menu.configure(state="normal" if keyboard else "disabled")
        self.usage_entry.configure(state="normal" if keyboard else "disabled")
        self.function_menu.configure(state="disabled" if keyboard else "normal")

    def _pick_key(self, name):
        self._replace_entry(self.usage_entry, f"0x{KEY_NAMES[name]:02X}")

    def _toggle_usage(self):
        if self.advanced_keys.get():
            self.usage_label.grid()
            self.usage_entry.grid()
        else:
            self.usage_label.grid_remove()
            self.usage_entry.grid_remove()

    def _restore_buttons(self):
        if messagebox.askyesno(
            "Varsayılan tuş düzeni",
            "Tüm tuş atamaları varsayılanlarla değiştirilecek. Devam edilsin mi?",
            parent=self.root,
        ):
            self._command("restore-buttons", {"persist": bool(self.persist_buttons.get())})

    def _save_onboard(self):
        if messagebox.askyesno(
            "Fare belleğine kaydet",
            "Mevcut cihaz ayarları fare belleğine kaydedilecek. Yazılım efektleri servis kapandığında devam etmez. Kaydedilsin mi?",
            parent=self.root,
        ):
            self._command("save")

    def _save_profile(self):
        name = self.profile_name.get()
        overwrite = name in self._profile_names
        if overwrite and not messagebox.askyesno(
            "Profili değiştir", f"{name!r} profilinin üzerine yazılsın mı?", parent=self.root
        ):
            return
        self._command("save-profile", {"name": name, "overwrite": overwrite})

    def _show_profile(self, name):
        if name == "Profil seç":
            return
        client = self.client

        def done(result):
            if self.profile_menu.get() == name:
                self._profile_records[name] = result["profile"]
                self._text(self.profile_detail, self._profile_summary(result["profile"]))
                self._status("Profil bilgileri yüklendi.")

        self._submit(
            lambda: require_ok(client("show-profile", {"name": name})),
            done,
        )

    @staticmethod
    def _profile_summary(profile):
        settings = profile["settings"]
        lines = [profile["name"], ""]
        if "dpi" in settings:
            dpi = settings["dpi"]
            lines.append("DPI: " + ", ".join(str(value) for value in dpi["stages"]))
            lines.append(f"Etkin kademe: {dpi['active'] + 1}")
        if "polling_rate" in settings:
            lines.append(f"Yoklama hızı: {settings['polling_rate']} Hz")
        if "buttons" in settings:
            lines.append(f"Tuş düzeni: {len(settings['buttons'])} atama")
        if "colors" in settings:
            lines.append(
                "RGB: "
                + ", ".join(f"{zone} {MuvvApp._hex(color)}" for zone, color in settings["colors"].items())
            )
        if profile["effect"]:
            effect = profile["effect"]["name"]
            label = next((label for label, name in EFFECT_NAMES.items() if name == effect), effect)
            lines.append(f"Aydınlatma: {label}")
        labels = {
            "dpi": "DPI",
            "polling_rate": "Yoklama hızı",
            "buttons": "Tuş düzeni",
            "colors": "RGB renkleri",
        }
        if profile["unknown_fields"]:
            lines.extend(
                [
                    "",
                    "Profilde bulunmayan ayarlar:",
                    ", ".join(labels[field] for field in profile["unknown_fields"]),
                ]
            )
        return "\n".join(lines)

    def _apply_profile(self):
        name = self.profile_menu.get()
        if name != "Profil seç":
            if self._dirty and not messagebox.askyesno(
                "Profili uygula",
                "Uygulanmamış girişler var. Profil uygulanırken bu girişler sıfırlansın mı?",
                parent=self.root,
            ):
                return
            self._command("apply-profile", {"name": name, "persist": bool(self.persist_profile.get())})

    def _delete_profile(self):
        name = self.profile_menu.get()
        if name == "Profil seç":
            return
        if messagebox.askyesno(
            "Profili sil", f"{name!r} profili bilgisayardan silinsin mi?", parent=self.root
        ):
            self._command("delete-profile", {"name": name}, device=False)

    def _rename_profile(self):
        name = self.profile_menu.get()
        if name == "Profil seç":
            return
        new_name = simpledialog.askstring(
            "Profilin adını değiştir", "Yeni profil adı:", initialvalue=name, parent=self.root
        )
        if new_name is not None:
            self._command("rename-profile", {"name": name, "new_name": new_name}, device=False)

    def _import_profile(self):
        filename = filedialog.askopenfilename(
            parent=self.root, title="Profil içe aktar", filetypes=[("JSON profili", "*.json")]
        )
        if not filename:
            return

        def prepared(profile):
            overwrite = profile["name"] in self._profile_names
            if overwrite and not messagebox.askyesno(
                "Profili değiştir", f"{profile['name']!r} zaten var. Üzerine yazılsın mı?", parent=self.root
            ):
                return
            self._command("import-profile", {"profile": profile, "overwrite": overwrite}, device=False)

        self._submit(lambda: read_profile_file(filename), prepared)

    def _export_profile(self):
        name = self.profile_menu.get()
        if name == "Profil seç":
            return
        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Profil dışa aktar",
            initialfile="muvv-profile.json",
            defaultextension=".json",
            filetypes=[("JSON profili", "*.json")],
        )
        if not filename:
            return
        client = self.client

        def task():
            profile = require_ok(client("show-profile", {"name": name}))["profile"]
            return write_profile_file(filename, profile, overwrite=True)

        self._submit(task, lambda result: self._status(f"Profil dışa aktarıldı: {result}"))

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._closed_event.set()
        self._callbacks.clear()
        self._pending_job = None
        for identifier in self._after_ids:
            self.root.after_cancel(identifier)
        # CustomTkinter also schedules appearance and scaling callbacks on this root.
        for identifier in self.root.tk.call("after", "info"):
            self.root.tk.call("after", "cancel", identifier)
        self._executor.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()
        gc.collect()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Muvv desktop controls")
    parser.add_argument(
        "--demo", action="store_true", help="Open an isolated demonstration without USB access"
    )
    options = parser.parse_args(argv)
    if not options.demo and not sys.platform.startswith("linux"):
        print("Cihaz kontrolü Linux gerektirir. Arayüzü denemek için muvv-gui --demo kullanın.")
        return 1
    if ctk is None:
        print("GUI dependency missing. Install the gui extra and your distribution's python3-tk package.")
        return 1
    ctk.set_appearance_mode("dark")
    demo_client = None
    try:
        if options.demo:
            from demo import DemoClient

            demo_client = DemoClient()
        try:
            root = ctk.CTk()
        except tk.TclError as error:
            print(f"Grafik ekran açılamadı: {error}", file=sys.stderr)
            return 1
        MuvvApp(root, client=demo_client or send_command, demo=options.demo)
        root.mainloop()
        return 0
    finally:
        if demo_client:
            demo_client.close()


if __name__ == "__main__":
    raise SystemExit(main())
