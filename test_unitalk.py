from src.upload_data.upload_unitalk import get_unitalk_all_data

def test_get_calls():
    """Тестуємо отримання дзвінків з Unitalk API"""
    print("🔄 Тестування отримання дзвінків з Unitalk API...")
    print("=" * 60)
    
    try:
        # Отримуємо дзвінки за сьогодні (менше даних для тесту)
        calls = get_unitalk_all_data(today=True)
        
        print("=" * 60)
        print(f"\n✅ Успішно отримано {len(calls)} дзвінків")
        
        if calls:
            print("\n📋 Перший дзвінок (приклад):")
            print("-" * 60)
            first_call = calls[0]
            for key, value in first_call.items():
                print(f"  {key}: {value}")
            print("-" * 60)
        else:
            print("⚠️ Дзвінків за сьогодні не знайдено")
            
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_calls()
