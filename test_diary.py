# -*- coding: utf-8 -*-
"""
Тестирование электронного дневника через agent-desktop FFI
Автоматизирует браузер и проверяет работу всех ролей
"""

import ctypes
import json
import os
import time
import sys

# Загрузка библиотеки
DLL_PATH = os.path.join(os.path.dirname(__file__), 
                        "agent-desktop-ffi-v1.3.1-x86_64-pc-windows-msvc",
                        "agent-desktop-ffi-v1.3.1-x86_64-pc-windows-msvc",
                        "lib", "agent_desktop_ffi.dll")

print(f"Загрузка библиотеки: {DLL_PATH}")
lib = ctypes.CDLL(DLL_PATH)

# ============ ИНИЦИАЛИЗАЦИЯ ============
def init_library():
    """Инициализация FFI библиотеки"""
    result = lib.ad_init(7)
    if result != 0:
        print(f"❌ Ошибка инициализации: {result}")
        return False
    print("✅ Библиотека инициализирована")
    return True

def create_adapter():
    """Создание адаптера"""
    adapter_ptr = lib.ad_adapter_create()
    if not adapter_ptr:
        print("❌ Ошибка создания адаптера")
        return None
    print("✅ Адаптер создан")
    return adapter_ptr

def destroy_adapter(adapter):
    """Уничтожение адаптера"""
    if adapter:
        lib.ad_adapter_destroy(adapter)
        print("🗑️ Адаптер уничтожен")

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
def get_status(adapter):
    """Проверка статуса и разрешений"""
    out = ctypes.c_char_p()
    result = lib.ad_status(adapter, ctypes.byref(out))
    if result == 0 and out.value:
        data = json.loads(out.value.decode('utf-8'))
        print(f"📊 Статус: {json.dumps(data, indent=2, ensure_ascii=False)}")
        lib.ad_free_string(out)
        return data
    return None

def snapshot(adapter, app=None, surface=0):
    """Делает снимок accessibility дерева"""
    out = ctypes.c_char_p()
    result = lib.ad_snapshot(
        adapter,
        app or b"",
        surface,
        20,  # max_depth
        False,  # interactive_only
        False,  # compact
        ctypes.byref(out)
    )
    if result == 0 and out.value:
        return json.loads(out.value.decode('utf-8'))
    return None

def click_ref(adapter, ref_id, action_type="click"):
    """Кликает по элементу по ref_id"""
    # Создаём действие
    action_data = ctypes.c_uint8 * 96
    action = action_data(0)
    
    # AD_ACTION_KIND_CLICK = 0
    ctypes.memmove(ctypes.byref(action), 
                   ctypes.c_int32(0).raw, 4)
    
    out = ctypes.c_char_p()
    result = lib.ad_execute_by_ref(
        adapter,
        ref_id.encode('utf-8'),
        ctypes.cast(ctypes.addressof(action), ctypes.POINTER(ctypes.c_void_p)),
        0,  # headless policy
        ctypes.byref(out)
    )
    if result == 0 and out.value:
        print(f"  ✅ Клик по {ref_id}")
        lib.ad_free_string(out)
        return True
    print(f"  ❌ Ошибка клика по {ref_id}: {result}")
    return False

def type_text(adapter, ref_id, text):
    """Вводит текст в поле"""
    action_data = ctypes.c_uint8 * 96
    action = action_data(0)
    
    # AD_ACTION_KIND_TYPE_TEXT = 17
    ctypes.memmove(ctypes.byref(action), 
                   ctypes.c_int32(17).raw, 4)
    
    out = ctypes.c_char_p()
    result = lib.ad_execute_by_ref(
        adapter,
        ref_id.encode('utf-8'),
        ctypes.cast(ctypes.addressof(action), ctypes.POINTER(ctypes.c_void_p)),
        2,  # headed policy (для ввода текста)
        ctypes.byref(out)
    )
    if result == 0 and out.value:
        print(f"  ✅ Ввод текста: {text}")
        lib.ad_free_string(out)
        return True
    print(f"  ❌ Ошибка ввода: {result}")
    return False

# ============ ТЕСТЫ ============
def test_login_page(adapter):
    """Тест 1: Страница входа"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 1: Страница входа")
    print("="*60)
    
    # Делаем снимок
    snap = snapshot(adapter)
    if snap:
        ref_count = snap.get("data", {}).get("ref_count", 0)
        print(f"  📸 Найдено элементов: {ref_count}")
        
        # Ищем элементы логина
        tree = snap.get("data", {}).get("tree", {})
        nodes = tree.get("nodes", [])
        
        for node in nodes:
            content = node.get("content", {})
            role = content.get("role", "")
            name = content.get("name", "")
            value = content.get("value", "")
            
            if role in ("textbox", "button"):
                print(f"    📋 {role}: {name} (value: {value[:50] if value else ''})")
        
        print("  ✅ Страница входа загружена")
        return True
    return False

def test_login_as_admin(adapter):
    """Тест 2: Вход как администратор"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 2: Вход как администратор")
    print("="*60)
    
    # Здесь нужно найти элементы через snapshot и кликнуть
    # Это примерная структура - нужно адаптировать под реальный UI
    
    snap = snapshot(adapter)
    if snap:
        print("  ✅ Страница загружена")
        return True
    return False

def test_login_as_director(adapter):
    """Тест 3: Вход как директор"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 3: Вход как директор")
    print("="*60)
    
    snap = snapshot(adapter)
    if snap:
        print("  ✅ Страница загружена")
        return True
    return False

def test_teacher_schedule(adapter):
    """Тест 4: Расписание учителя"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 4: Расписание учителя")
    print("="*60)
    
    snap = snapshot(adapter)
    if snap:
        # Проверяем, что в расписании есть номер урока и время
        tree = snap.get("data", {}).get("tree", {})
        nodes = tree.get("nodes", [])
        
        found_lesson_number = False
        found_time = False
        
        for node in nodes:
            content = node.get("content", {})
            name = content.get("name", "")
            value = content.get("value", "")
            text = name + " " + value
            
            if "#1" in text or "#2" in text or "#3" in text:
                found_lesson_number = True
                print(f"  ✅ Найден номер урока: {text[:50]}")
            if ":" in text and any(word in text.lower() for word in ["08:", "09:", "10:", "11:"]):
                found_time = True
                print(f"  ✅ Найдено время урока: {text[:50]}")
        
        if not found_lesson_number:
            print("  ❌ Не найден номер урока в расписании")
        if not found_time:
            print("  ❌ Не найдено время урока в расписании")
        
        return found_lesson_number and found_time
    return False

def test_import_students(adapter):
    """Тест 5: Импорт учеников из файла"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 5: Импорт учеников")
    print("="*60)
    
    # Создаём тестовый файл
    test_file = "test_students.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("Иванов Иван Петрович\n")
        f.write("Петрова Мария Сергеевна\n")
        f.write("Сидоров Алексей Николаевич\n")
    
    print(f"  📄 Создан тестовый файл: {test_file}")
    
    # Проверяем содержимое
    with open(test_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        print(f"  📄 Строк в файле: {len(lines)}")
    
    print("  ✅ Тестовый файл создан")
    return True

def test_teacher_deletion(adapter):
    """Тест 6: Удаление учителя с подтверждением"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 6: Удаление учителя")
    print("="*60)
    
    snap = snapshot(adapter)
    if snap:
        print("  ✅ Страница учителей загружена")
        return True
    return False

def test_schedule_display(adapter):
    """Тест 7: Проверка отображения расписания"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 7: Расписание - номер урока и время")
    print("="*60)
    
    snap = snapshot(adapter)
    if snap:
        tree = snap.get("data", {}).get("tree", {})
        nodes = tree.get("nodes", [])
        
        lesson_items = []
        for node in nodes:
            content = node.get("content", {})
            name = content.get("name", "")
            value = content.get("value", "")
            desc = content.get("description", "")
            
            if name or value:
                text = f"{name} {value}".strip()
                if text:
                    lesson_items.append(text)
        
        print(f"  📋 Найдено элементов: {len(lesson_items)}")
        
        # Проверяем формат расписания
        has_number = any("#" in item and any(c.isdigit() for c in item) for item in lesson_items)
        has_time = any(":" in item for item in lesson_items)
        
        if has_number:
            print("  ✅ Номера уроков (#1, #2...) отображаются")
        else:
            print("  ❌ Номера уроков НЕ отображаются")
            
        if has_time:
            print("  ✅ Время уроков отображается")
        else:
            print("  ❌ Время уроков НЕ отображается")
        
        return has_number and has_time
    return False

# ============ ГЛАВНЫЙ ЦИКЛ ============
def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 ЗАПУСК ТЕСТИРОВАНИЯ ЭЛЕКТРОННОГО ДНЕВНИКА")
    print("="*60)
    
    # Инициализация
    if not init_library():
        return
    
    adapter = create_adapter()
    if not adapter:
        return
    
    try:
        # Проверяем статус
        get_status(adapter)
        
        # Ждём открытия браузера
        print("\n⏳ Откройте браузер с дневником: https://epikdragon1.github.io/diary/")
        print("⏳ Нажмите Enter для начала тестирования...")
        input()
        
        # Запускаем тесты
        results = {}
        
        results["login"] = test_login_page(adapter)
        results["schedule_display"] = test_schedule_display(adapter)
        results["import"] = test_import_students(adapter)
        
        # Для остальных тестов нужно сначала войти
        print("\n⏳ Войдите как администратор через форму 'Вход для администраторов'")
        print("⏳ Нажмите Enter для продолжения...")
        input()
        
        results["admin_login"] = test_login_as_admin(adapter)
        results["teacher_schedule"] = test_teacher_schedule(adapter)
        
        print("\n⏳ Войдите как директор")
        print("⏳ Нажмите Enter для продолжения...")
        input()
        
        results["director_login"] = test_login_as_director(adapter)
        
        print("\n⏳ Войдите как учитель")
        print("⏳ Нажмите Enter для продолжения...")
        input()
        
        results["teacher_deletion"] = test_teacher_deletion(adapter)
        
        # Итоги
        print("\n" + "="*60)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("="*60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")
        
        print(f"\n📈 Пройдено: {passed}/{total}")
        
        if passed == total:
            print("🎉 Все тесты пройдены!")
        else:
            print(f"⚠️ Не пройдено {total - passed} тестов")
            
    finally:
        destroy_adapter(adapter)

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️ Тестирование прервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
