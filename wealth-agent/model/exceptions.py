
def _format_entity_option(opt: dict) -> str:
    if '基金公司全称' in opt:
        return opt.get('基金公司全称', '')
    short = opt.get('基金简称', '')
    code = opt.get('基金代码', '')
    return f'{short}({code})' if code else short

class EntityConflictError(Exception):

    def __init__(self, entity_name: str=None, options: list=None, conflicts: list=None, message: str=None):
        self.entity_name = entity_name
        self.options = options
        self.conflicts = conflicts
        if message is None:
            if conflicts:
                sections = []
                for c in conflicts:
                    entity = c['entity_name']
                    opts = c['options']
                    numbered = [f'  {i + 1}. {_format_entity_option(o)}' for i, o in enumerate(opts)]
                    sections.append(f"根据识别到的 '{entity}' 匹配到了{len(opts)}个实体名称：\n" + '\n'.join(numbered))
                message = '\n\n'.join(sections) + '\n\n**请从其中选择你想查询的实体**。'
            else:
                numbered = [f'  {i + 1}. {_format_entity_option(o)}' for i, o in enumerate(options)]
                message = f"根据识别到的 '{entity_name}' 匹配到了{len(options)}个实体名称：\n" + '\n'.join(numbered) + '\n\n**请从其中选择你想查询的实体**。'
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

    def __repr__(self):
        if self.conflicts:
            return f'EntityConflictError(conflicts={self.conflicts})'
        return f"EntityConflictError(entity_name='{self.entity_name}', options={self.options})"

class TokenInvalidError(Exception):

    def __init__(self, code: str, msg: str, message: str=None):
        self.code = code
        self.msg = msg
        if message is None:
            message = f'Token无效: {code} - {msg}'
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

    def __repr__(self):
        return f"TokenInvalidError(code='{self.code}', msg='{self.msg}')"
