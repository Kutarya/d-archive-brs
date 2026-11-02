import argparse
import gc
import queue
from concurrent.futures import ThreadPoolExecutor

from animations.effect_registry import create_effect
from cli import send_command
from managers.errors import MuvvError
from managers.validator import rgb

try:
    import tkinter as tk
    from tkinter import colorchooser, messagebox

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
        self._buttons = []
        self._devices = {}
        self._device_id = None
        self._state = {}
        self._capabilities = {}
        self._preview_effect = None
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

    def _schedule(self, delay, callback):
        if not self._closed:

            def run():
                self._after_ids.discard(identifier)
                if not self._closed:
                    callback()

            identifier = self.root.after(delay, run)
            self._after_ids.add(identifier)

    def _button(self, parent, text, command, secondary=False, **kwargs):
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
        self._buttons.append(button)
        return button

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
        self._button(sidebar, "Cihazları yenile", self.refresh, secondary=True).grid(
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
            sidebar, "Cihazı yeniden bağla", lambda: self._command("reconnect"), secondary=True
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
        for name in ("Aydınlatma", "DPI ve hız", "Tuşlar", "Profiller"):
            self.tabs.add(name).grid_columnconfigure(0, weight=1)
        self._lighting(self.tabs.tab("Aydınlatma"))
        self._dpi(self.tabs.tab("DPI ve hız"))
        self._keys(self.tabs.tab("Tuşlar"))
        self._profiles(self.tabs.tab("Profiller"))
        self.status_label = self._label(
            main, "Hazırlanıyor…", color=MUTED, anchor="w", wraplength=690, justify="left"
        )
        self.status_label.grid(row=3, column=0, sticky="ew", pady=(16, 0))

    def _lighting(self, tab):
        self._label(tab, "RGB efekti", 19, anchor="w").grid(
            row=0, column=0, padx=22, pady=(18, 0), sticky="ew"
        )
        self.preview = tk.Canvas(tab, height=128, bg=PANEL, highlightthickness=0)
        self.preview.grid(row=1, column=0, padx=22, pady=12, sticky="ew")
        self._preview_items = []
        for index, name in enumerate(("Tekerlek", "Orta", "Alt")):
            x = 92 + index * 190
            item = self.preview.create_rectangle(x - 45, 20, x + 45, 79, fill="#4AD2B1", outline="")
            self.preview.create_text(x, 104, text=name, fill=MUTED, font=("Segoe UI", 11))
            self._preview_items.append(item)
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
        self.color_entry.pack(side="left")
        self._button(color_frame, "Renk seç", self._choose_color, secondary=True, width=100).pack(
            side="left", padx=10
        )
        self._label(fields, "Hız").grid(row=2, column=0, sticky="w", pady=9)
        self.speed = ctk.CTkSlider(fields, from_=0, to=20, number_of_steps=400)
        self.speed.set(1)
        self.speed.grid(row=2, column=1, padx=(20, 0), sticky="ew")
        self._label(fields, "Dalga yönü").grid(row=3, column=0, sticky="w", pady=9)
        self.direction = ctk.CTkOptionMenu(fields, values=["Dikey", "Yatay"])
        self.direction.grid(row=3, column=1, padx=(20, 0), sticky="ew")
        self._label(fields, "Dalga boyu").grid(row=4, column=0, sticky="w", pady=9)
        self.wave_length = ctk.CTkEntry(fields)
        self.wave_length.insert(0, "0.5")
        self.wave_length.grid(row=4, column=1, padx=(20, 0), sticky="ew")
        self._label(fields, "Spektrum parlaklığı").grid(row=5, column=0, sticky="w", pady=9)
        self.brightness = ctk.CTkSlider(fields, from_=0, to=1, number_of_steps=100)
        self.brightness.set(1)
        self.brightness.grid(row=5, column=1, padx=(20, 0), sticky="ew")
        actions = ctk.CTkFrame(tab, fg_color="transparent")
        actions.grid(row=3, column=0, padx=22, pady=(22, 12), sticky="ew")
        self._button(actions, "Efekti uygula", self._apply_effect).pack(side="left")
        self._button(actions, "Mevcut efekti güncelle", self._update_effect, secondary=True).pack(
            side="left", padx=12
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
            entry.grid(row=1, column=index, padx=5, sticky="ew")
            self.dpi_entries.append(entry)
        active = ctk.CTkFrame(tab, fg_color="transparent")
        active.grid(row=3, column=0, padx=22, sticky="ew")
        self._label(active, "Etkin kademe").pack(side="left")
        self.active_stage = ctk.CTkOptionMenu(active, values=["1", "2", "3", "4", "5"], width=95)
        self.active_stage.pack(side="left", padx=20)
        self._button(active, "Beş kademeyi uygula", self._apply_dpi).pack(side="right")
        self.dpi_range = self._label(
            tab, "Rival 3 Gen 2: 200–8500 DPI, 100 DPI adımlarla.", color=MUTED, anchor="w"
        )
        self.dpi_range.grid(row=4, column=0, padx=22, pady=(15, 30), sticky="ew")
        self._label(tab, "Yoklama hızı", 19, anchor="w").grid(row=5, column=0, padx=22, sticky="ew")
        polling = ctk.CTkFrame(tab, fg_color="transparent")
        polling.grid(row=6, column=0, padx=22, pady=18, sticky="ew")
        self.polling_menu = ctk.CTkOptionMenu(polling, values=["Bilinmiyor", "125", "250", "500", "1000"])
        self.polling_menu.pack(side="left")
        self._button(polling, "Hızı uygula", self._apply_polling).pack(side="right")

    def _keys(self, tab):
        self._label(tab, "Klavye tuşu atama", 19, anchor="w").grid(
            row=0, column=0, padx=22, pady=(22, 10), sticky="ew"
        )
        self._label(
            tab,
            "HID tuş kodu kullanılır. Örnek: A = 0x04, Enter = 0x28, sol Shift = 0xE1.",
            color=MUTED,
            wraplength=640,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, padx=22, sticky="ew")
        fields = ctk.CTkFrame(tab, fg_color="transparent")
        fields.grid(row=2, column=0, padx=22, pady=24, sticky="ew")
        self.button_menu = ctk.CTkOptionMenu(fields, values=list(BUTTON_NAMES))
        self.button_menu.set("Yan / geri")
        self.button_menu.pack(side="left")
        self.usage_entry = ctk.CTkEntry(fields, width=130, placeholder_text="0x04")
        self.usage_entry.insert(0, "0x04")
        self.usage_entry.pack(side="left", padx=16)
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
        self._button(actions, "Profili sil", self._delete_profile, secondary=True).pack(side="left", padx=12)
        self.profile_detail = ctk.CTkTextbox(tab, height=195, fg_color=BACKGROUND)
        self.profile_detail.grid(row=6, column=0, padx=22, pady=20, sticky="ew")

    def _status(self, message, error=False):
        self.status_label.configure(text=message, text_color="#FFAD9C" if error else MUTED)

    def _submit(self, task, callback):
        if self._busy or self._closed:
            return
        # Reclaim unused Tk resources on the UI thread before allocating in the I/O worker.
        gc.collect()
        self._busy = True
        for button in self._buttons:
            button.configure(state="disabled")
        self._status("İşlem sürüyor…")
        future = self._executor.submit(task)
        future.add_done_callback(lambda completed: self._results.put((completed, callback)))

    def _poll_results(self):
        if self._closed:
            return
        try:
            future, callback = self._results.get_nowait()
        except queue.Empty:
            pass
        else:
            self._busy = False
            for button in self._buttons:
                button.configure(state="normal")
            try:
                callback(future.result())
            except Exception as error:
                self._status(str(error), error=True)
        self._schedule(50, self._poll_results)

    @staticmethod
    def _require_ok(response):
        if response.get("status") != "ok":
            raise ValueError(response.get("message", "İşlem tamamlanamadı."))
        return response

    def refresh(self):
        selected = self._device_id

        def task():
            devices = self._require_ok(self.client("list")).get("devices", [])
            profiles = self._require_ok(self.client("list-profiles")).get("profiles", [])
            available = [device["id"] for device in devices]
            current = selected if selected in available else (available[0] if available else None)
            info = self._require_ok(self.client("info", {"device": current})) if current else None
            return devices, profiles, current, info

        self._submit(task, self._refreshed)

    def _refreshed(self, result):
        devices, profiles, selected, info = result
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
        names = [profile["name"] for profile in profiles] or ["Profil seç"]
        self.profile_menu.configure(values=names)
        if self.profile_menu.get() not in names:
            self.profile_menu.set(names[0])
        if info is None:
            self.device_detail.configure(text="Desteklenen fare bulunamadı.")
            self._status("Cihazı bağladıktan sonra yenileyin.")
            self._state = {}
            self._capabilities = {}
            self._preview_effect = None
            return
        self._load_info(info)
        self._status(
            "Cihaz ayarları güncel."
            if not self.demo
            else "Demo hazır. Değişiklikler yalnızca bu pencerenin oturumunda uygulanır."
        )

    def _select_device(self, label):
        if self._busy:
            self.device_menu.set(
                next((name for name, identity in self._devices.items() if identity == self._device_id), label)
            )
            return
        self._device_id = self._devices.get(label)
        self.refresh()

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
        if dpi:
            for entry, value in zip(self.dpi_entries, dpi["stages"], strict=True):
                entry.delete(0, "end")
                entry.insert(0, str(value))
            self.active_stage.set(str(dpi["active"] + 1))
            self.dpi_note.configure(text="Bu oturumda uygulanan beş DPI kademesi.")
        else:
            self.dpi_note.configure(
                text="Faredeki değerler okunamaz. Bu alanlar önerilen başlangıç değerleridir."
            )
        self.polling_menu.set(str(settings.get("polling_rate", "Bilinmiyor")))
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
        if effect:
            self.effect_menu.set(
                next(
                    (name for name, identifier in EFFECT_NAMES.items() if identifier == effect["name"]),
                    "Sabit",
                )
            )
            options = effect["options"]
            if "color" in options:
                self.color_entry.delete(0, "end")
                self.color_entry.insert(0, "#" + "".join(f"{channel:02X}" for channel in options["color"]))
            if "speed" in options:
                self.speed.set(options["speed"])
            if "brightness" in options:
                self.brightness.set(options["brightness"])
            if "direction" in options:
                self.direction.set("Yatay" if options["direction"] == "horizontal" else "Dikey")
                self.wave_length.delete(0, "end")
                self.wave_length.insert(0, str(options["wave_length"]))
            self._preview_effect = create_effect(effect["name"], options)
            self._effect_changed()
        else:
            self._preview_effect = None

    @staticmethod
    def _text(widget, value):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    @staticmethod
    def _button_label(value):
        if isinstance(value, (tuple, list)):
            return f"Klavye tuşu 0x{value[1]:02X}"
        return {
            0: "Devre dışı",
            1: "Sol tık",
            2: "Sağ tık",
            3: "Orta tık",
            4: "Geri",
            5: "İleri",
            48: "DPI değiştir",
            49: "Yukarı kaydır",
            50: "Aşağı kaydır",
        }.get(value, str(value))

    def _command(self, command, args=None):
        if self._device_id is None:
            self._status("Önce bağlı bir cihaz seçin.", error=True)
            return
        selected = self._device_id
        payload = {"device": selected, **(args or {})}

        def task():
            response = self._require_ok(self.client(command, payload))
            info = self._require_ok(self.client("info", {"device": selected}))
            profiles = self._require_ok(self.client("list-profiles")).get("profiles", [])
            return response, info, profiles

        def done(result):
            response, info, profiles = result
            self._load_info(info)
            names = [profile["name"] for profile in profiles] or ["Profil seç"]
            self.profile_menu.configure(values=names)
            if self.profile_menu.get() not in names:
                self.profile_menu.set(names[0])
            message = "Ayar uygulandı."
            if response.get("persistence_requested"):
                message = "Ayar uygulandı ve fareye kaydetme komutu gönderildi."
            if command == "save-profile":
                message = "Profil bilgisayara kaydedildi."
            self._status(message)

        self._submit(task, done)

    def _effect_changed(self, *_):
        effect = EFFECT_NAMES[self.effect_menu.get()]
        self.color_entry.configure(state="normal" if effect != "spectrum" else "disabled")
        self.speed.configure(state="normal" if effect != "static" else "disabled")
        self.direction.configure(state="normal" if effect == "wave" else "disabled")
        self.wave_length.configure(state="normal" if effect == "wave" else "disabled")
        self.brightness.configure(state="normal" if effect == "spectrum" else "disabled")

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
        color = colorchooser.askcolor(
            parent=self.root, initialcolor=self.color_entry.get(), title="RGB rengi"
        )[1]
        if color:
            self.color_entry.delete(0, "end")
            self.color_entry.insert(0, color.upper())

    def _animate_preview(self):
        if self._closed:
            return
        if self._preview_effect:
            colors = self._preview_effect.apply(3, [(0.5, 0.1), (0.5, 0.5), (0.5, 0.9)])
        else:
            colors = [(43, 55, 67)] * 3
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
        self._command("save-profile", {"name": self.profile_name.get()})

    def _show_profile(self, name):
        if name == "Profil seç":
            return
        self._submit(
            lambda: self._require_ok(self.client("show-profile", {"name": name})),
            lambda result: (
                self._text(self.profile_detail, self._profile_summary(result["profile"])),
                self._status("Profil bilgileri yüklendi."),
            ),
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
            self._command("apply-profile", {"name": name, "persist": bool(self.persist_profile.get())})

    def _delete_profile(self):
        name = self.profile_menu.get()
        if name == "Profil seç":
            return
        if messagebox.askyesno(
            "Profili sil", f"{name!r} profili bilgisayardan silinsin mi?", parent=self.root
        ):
            self._submit(
                lambda: self._require_ok(self.client("delete-profile", {"name": name})),
                lambda _: self.refresh(),
            )

    def close(self):
        if self._closed:
            return
        self._closed = True
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
    if ctk is None:
        print("GUI dependency missing. Install the gui extra and your distribution's python3-tk package.")
        return 1
    ctk.set_appearance_mode("dark")
    demo_client = None
    try:
        if options.demo:
            from demo import DemoClient

            demo_client = DemoClient()
        root = ctk.CTk()
        MuvvApp(root, client=demo_client or send_command, demo=options.demo)
        root.mainloop()
        return 0
    finally:
        if demo_client:
            demo_client.close()


if __name__ == "__main__":
    raise SystemExit(main())
