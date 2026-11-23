import * as vscode from 'vscode';

const cfg = () => vscode.workspace.getConfiguration('legacy2modern');

async function api(path: string, options: RequestInit = {}): Promise<any> {
  const base = cfg().get<string>('apiBase') || 'http://localhost:8000';
  const token = cfg().get<string>('token') || '';
  const res = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json();
}

export function activate(context: vscode.ExtensionContext) {
  const login = vscode.commands.registerCommand('legacy2modern.login', async () => {
    const email = await vscode.window.showInputBox({ prompt: '输入邮箱注册/登录' });
    if (!email) return;
    try {
      const data = await api('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
      await cfg().update('token', data.token, vscode.ConfigurationTarget.Global);
      vscode.window.showInformationMessage(`登录成功，赠送 ${data.credits} 点数`);
    } catch (e: any) {
      vscode.window.showErrorMessage(e.message);
    }
  });

  const refactor = vscode.commands.registerCommand('legacy2modern.refactor', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    const selection = editor.selection;
    const selected = editor.document.getText(selection);
    if (!selected.trim()) {
      vscode.window.showWarningMessage('请先选中要重构的代码');
      return;
    }
    const target = await vscode.window.showQuickPick(
      ['springboot3', 'vue3', 'python3'],
      { placeHolder: '选择目标技术栈' }
    );
    if (!target) return;

    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: 'AI 正在重构代码…', cancellable: false },
      async () => {
        try {
          const data = await api('/refactor', {
            method: 'POST',
            body: JSON.stringify({
              source_code: selected,
              from_stack: 'java8',
              to_stack: target,
            }),
          });
          const doc = await vscode.workspace.openTextDocument({ content: data.result, language: 'java' });
          await vscode.window.showTextDocument(doc, { preview: false, viewColumn: vscode.ViewColumn.Beside });
          vscode.window.showInformationMessage(`重构完成，剩余点数：${data.credits_left}`);
        } catch (e: any) {
          vscode.window.showErrorMessage(e.message);
        }
      }
    );
  });

  context.subscriptions.push(login, refactor);
}

export function deactivate() {}
