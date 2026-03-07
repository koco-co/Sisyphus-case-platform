def validate_case_quality(case: dict) -> list[str]:
    errors: list[str] = []
    expected_results = (case.get('expected_results') or '').strip()
    if expected_results in {'系统处理成功', '结果正确', '页面显示正常'}:
        errors.append('expected_results_too_vague')
    if not case.get('steps'):
        errors.append('steps_missing')
    return errors
