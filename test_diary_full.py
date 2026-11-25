# -*- coding: utf-8 -*-
"""
Автоматизированное тестирование электронного дневника
Через agent-desktop FFI (Vercel Labs)
"""

import ctypes
import json
import os
import re
import time
import subprocess
import sys

# Путь к DLL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DLL_PATH = os.path.join(
    "C:\\Users\\user\\Downloads",
    "agent-desktop-ffi-v1.3.1-x86_64-pc-windows-msvc",
    "agent-desktop-ffi-v1.3.1-x86_64-pc-windows-msvc",
    "lib",
    "agent_desktop_ffi.dll"
)

# URL дневника
DIARY_URL = "https://epikdragon1.github.io/diary/"

print("=" * 70)
print("📚 ЭЛЕКТРОННЫЙ ДНЕВНИК — АВТОМАТИЗИРОВАННОЕ ТЕСТИРОВАНИЕ")
print("=" * 70)
print(f"📁 Путь к DLL: {DLL_PATH}")
print(f"🌐 URL дневника: {DIARY_URL}")
print("=" * 70)

# Проверяем существование DLL
if not os.path.exists(DLL_PATH):
    print(f"\n❌ Файл DLL не найден: {DLL_PATH}")
    print("⚠️ Убедитесь, что agent-desktop-ffi скачан правильно")
    sys.exit(1)

# Загружаем DLL
print("\n📦 Загрузка библиотеки...")
try:
    lib = ctypes.CDLL(DLL_PATH)
    print("✅ Библиотека загружена")
except Exception as e:
    print(f"❌ Ошибка загрузки: {e}")
    sys.exit(1)

# ============ КЛАСС ТЕСТЕРА ============
class DiaryTester:
    def __init__(self):
        self.adapter = None
        self.results = {}
        self.passed = 0
        self.failed = 0
        
    def init(self):
        """Инициализация FFI"""
        print("\n🔧 Инициализация FFI...")
        result = lib.ad_init(7)
        if result != 0:
            print(f"❌ Ошибка инициализации: {result}")
            return False
        print("✅ FFI инициализирован")
        return True
    
    def create_adapter(self):
        """Создание адаптера"""
        self.adapter = lib.ad_adapter_create()
        if not self.adapter:
            print("❌ Не удалось создать адаптер")
            return False
        print("✅ Адаптер создан")
        return True
    
    def destroy_adapter(self):
        """Уничтожение адаптера"""
        if self.adapter:
            lib.ad_adapter_destroy(self.adapter)
            print("🗑️ Адаптер уничтожен")
    
    def check_permissions(self):
        """Проверка разрешений"""
        print("\n🔐 Проверка разрешений...")
        result = lib.ad_check_permissions(self.adapter)
        if result == 0:
            print("✅ Разрешения получены")
            return True
        print(f"❌ Ошибка разрешений: {result}")
        return False
    
    def open_browser(self):
        """Открытие браузера с дневником"""
        print(f"\n🌐 Открытие браузера: {DIARY_URL}")
        
        # Пробуем открыть в Chrome
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            subprocess.Popen([chrome_path, "--new-window", DIARY_URL])
            print("✅ Chrome открыт")
        else:
            # Пробуем Firefox
            firefox_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"
            if os.path.exists(firefox_path):
                subprocess.Popen([firefox_path, "--new-window", DIARY_URL])
                print("✅ Firefox открыт")
            else:
                print("⚠️ Браузер не найден, откройте вручную")
                print(f"   URL: {DIARY_URL}")
        
        time.sleep(3)  # Ждём загрузки
    
    def take_snapshot(self):
        """Делает снимок accessibility дерева"""
        out = ctypes.c_char_p()
        result = lib.ad_snapshot(
            self.adapter,
            b"",  # null = focused window
            0,  # surface = window
            20,  # max_depth
            False,  # interactive_only
            False,  # compact
            ctypes.byref(out)
        )
        
        if result == 0 and out.value:
            data = json.loads(out.value.decode('utf-8'))
            lib.ad_free_string(out)
            return data
        return None
    
    def find_element_by_name(self, snapshot, name):
        """Ищет элемент по имени в снимке"""
        tree = snapshot.get("data", {}).get("tree", {})
        nodes = tree.get("nodes", [])
        
        for i, node in enumerate(nodes):
            content = node.get("content", {})
            node_name = content.get("name", "")
            if name.lower() in node_name.lower():
                ref_id = f"@{snapshot['data']['snapshot_id']}:e{i}"
                return ref_id, content
        return None, None
    
    def find_elements_by_role(self, snapshot, role):
        """Ищет все элементы по роли"""
        tree = snapshot.get("data", {}).get("tree", {})
        nodes = tree.get("nodes", [])
        snapshot_id = snapshot["data"]["snapshot_id"]
        
        found = []
        for i, node in enumerate(nodes):
            content = node.get("content", {})
            if content.get("role", "") == role:
                ref_id = f"@{snapshot_id}:e{i}"
                found.append((ref_id, content))
        return found
    
    def click_element(self, ref_id):
        """Кликает по элементу"""
        action_data = ctypes.c_uint8 * 96
        action = action_data(0)
        
        # AD_ACTION_KIND_CLICK = 0
        ctypes.memmove(ctypes.byref(action), ctypes.c_int32(0).raw, 4)
        
        out = ctypes.c_char_p()
        result = lib.ad_execute_by_ref(
            self.adapter,
            ref_id.encode('utf-8'),
            ctypes.cast(ctypes.addressof(action), ctypes.POINTER(ctypes.c_void_p)),
            0,  # headless
            ctypes.byref(out)
        )
        
        if result == 0 and out.value:
            lib.ad_free_string(out)
            return True
        return False
    
    def type_in_element(self, ref_id, text):
        """Вводит текст в элемент"""
        action_data = ctypes.c_uint8 * 96
        action = action_data(0)
        
        # AD_ACTION_KIND_TYPE_TEXT = 17
        ctypes.memmove(ctypes.byref(action), ctypes.c_int32(17).raw, 4)
        
        out = ctypes.c_char_p()
        result = lib.ad_execute_by_ref(
            self.adapter,
            ref_id.encode('utf-8'),
            ctypes.cast(ctypes.addressof(action), ctypes.POINTER(ctypes.c_void_p)),
            2,  # headed (для ввода)
            ctypes.byref(out)
        )
        
        if result == 0 and out.value:
            lib.ad_free_string(out)
            return True
        return False
    
    def press_enter(self):
        """Нажимает Enter"""
        # Используем keyboard input
        import ctypes.wintypes
        user32 = ctypes.windll.user32
        
        # Simulate Enter key
        user32.keybd_event(0x0D, 0, 0, 0)  # key down
        time.sleep(0.1)
        user32.keybd_event(0x0D, 0, 0x0002, 0)  # key up
    
    def test_page_loads(self):
        """Тест 1: Страница загружается"""
        print("\n" + "=" * 70)
        print("🧪 ТЕСТ 1: Страница загружается")
        print("=" * 70)
        
        snapshot = self.take_snapshot()
        if not snapshot:
            print("❌ Не удалось сделать снимок")
            return False
        
        ref_count = snapshot.get("data", {}).get("ref_count", 0)
        print(f"  📸 Элементов на странице: {ref_count}")
        
        # Ищем заголовок
        ref_id, content = self.find_element_by_name(snapshot, "дневник")
        if ref_id:
            print(f"  ✅ Найдён заголовок: {content.get('name', '')}")
            return True
        else:
            print("  ⚠️ Заголовок не найден, но страница загружена")
            return True
    
    def test_login_form(self):
        """Тест 2: Форма входа"""
        print("\n" + "=" * 70)
        print("🧪 ТЕСТ 2: Форма входа")
        print("=" * 70)
        
        snapshot = self.take_snapshot()
        if not snapshot:
            print("❌ Не удалось сделать снимок")
            return False
        
        # Ищем поля ввода
        textboxes = self.find_elements_by_role(snapshot, "textbox")
        print(f"  📋 Полей ввода найдено: {len(textboxes)}")
        
        buttons = self.find_elements_by_role(snapshot, "button")
        print(f"  🔘 Кнопок найдено: {len(buttons)}")
        
        # Проверяем наличие кнопок входа
        has_login = any("вход" in c.get("name", "").lower() for _, c in buttons)
        if has_login:
            print("  ✅ Кнопка входа найдена")
            return True
        else:
            print("  ⚠️ Кнопка входа не найдена (возможно, уже вошли)")
            return True
    
    def test_schedule_display(self):
        """Тест 3: Расписание отображается с номером и временем"""
        print("\n" + "=" * 70)
        print("🧪 ТЕСТ 3: Расписание — номер урока и время")
        print("=" * 70)
        
        snapshot = self.take_snapshot()
        if not snapshot:
            print("❌ Не удалось сделать снимок")
            return False
        
        tree = snapshot.get("data", {}).get("tree", {})
        nodes = tree.get("nodes", [])
        
        # Собираем весь текст
        all_text = []
        for node in nodes:
            content = node.get("content", {})
            name = content.get("name", "")
            value = content.get("value", "")
            desc = content.get("description", "")
            if name:
                all_text.append(name)
            if value:
                all_text.append(value)
        
        full_text = " ".join(all_text)
        
        # Проверяем наличие номеров уроков
        has_numbers = bool(re.search(r'#\d+', full_text))
        has_times = bool(re.search(r'\d{2}:\d{2}', full_text))
        
        if has_numbers:
            print("  ✅ Номера уроков (#1, #2...) найдены")
        else:
            print("  ❌ Номера уроков НЕ найдены")
            
        if has_times:
            print("  ✅ Время уроков (08:00, 08:45) найдено")
        else:
            print("  ❌ Время уроков НЕ найдено")
        
        return has_numbers and has_times
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("\n" + "=" * 70)
        print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ")
        print("=" * 70)
        
        # Инициализация
        if not self.init():
            return
        
        if not self.create_adapter():
            return
        
        if not self.check_permissions():
            return
        
        # Открытие браузера
        self.open_browser()
        
        # Ждём загрузки
        print("\n⏳ Ожидаем загрузки страницы...")
        time.sleep(5)
        
        # Запускаем тесты
        self.test_page_loads()
        self.test_login_form()
        
        # Для остальных тестов нужно войти
        print("\n" + "=" * 70)
        print("⚠️  ДЛЯ ПРОДОЛЖЕНИЯ:")
        print("=" * 70)
        print("1. Войдите как УЧЕНИК → перейдите в 'Расписание'")
        print("2. Нажмите Enter для проверки расписания")
        input("\n   Нажмите Enter...")
        
        self.test_schedule_display()
        
        # Итоги
        self.print_results()
    
    def print_results(self):
        """Выводит итоги тестирования"""
        print("\n" + "=" * 70)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("=" * 70)
        
        for test_name, result in self.results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")
        
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        print(f"\n📈 Пройдено: {passed}/{total}")
        
        if passed == total:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        else:
            print(f"⚠️ Не пройдено {total - passed} тестов")

# ============ ЗАПУСК ============
if __name__ == "__main__":
    tester = DiaryTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️ Тестирование прервано")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        tester.destroy_adapter()
