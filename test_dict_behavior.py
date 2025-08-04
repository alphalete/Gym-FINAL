#!/usr/bin/env python3
"""
Test to verify the root cause of the amount_owed issue
"""

def test_dict_get_behavior():
    """Test how dict.get() behaves with None values"""
    print("🔍 TESTING DICT.GET() BEHAVIOR WITH NONE VALUES")
    print("=" * 60)
    
    # Simulate the current problematic logic
    client_dict = {
        'monthly_fee': 55.0,
        'amount_owed': None,  # This is what's coming from the request
        'payment_status': 'due'
    }
    
    print(f"client_dict: {client_dict}")
    
    # Current logic (problematic)
    current_logic_result = client_dict.get('amount_owed', client_dict['monthly_fee'])
    print(f"Current logic result: {current_logic_result}")
    print(f"Current logic result type: {type(current_logic_result)}")
    
    # Fixed logic (what should happen)
    if client_dict.get('amount_owed') is None:
        fixed_logic_result = client_dict['monthly_fee']
    else:
        fixed_logic_result = client_dict['amount_owed']
    
    print(f"Fixed logic result: {fixed_logic_result}")
    print(f"Fixed logic result type: {type(fixed_logic_result)}")
    
    print("\n🔍 ANALYSIS:")
    print(f"- dict.get('amount_owed', default) returns: {current_logic_result}")
    print("- This is because None is a valid value in the dict, so .get() doesn't use the default")
    print("- We need to explicitly check if the value is None")
    
    # Test with missing key
    client_dict_no_amount = {
        'monthly_fee': 55.0,
        'payment_status': 'due'
        # amount_owed key is missing
    }
    
    print(f"\nTesting with missing amount_owed key:")
    print(f"client_dict_no_amount: {client_dict_no_amount}")
    missing_key_result = client_dict_no_amount.get('amount_owed', client_dict_no_amount['monthly_fee'])
    print(f"Result with missing key: {missing_key_result}")
    print("- This works correctly because the key doesn't exist")

if __name__ == "__main__":
    test_dict_get_behavior()