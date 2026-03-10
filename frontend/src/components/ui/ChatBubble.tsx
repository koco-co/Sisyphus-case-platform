const CHECK_SVG =
  '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:2px"><polyline points="20 6 9 17 4 12"/></svg>';

interface ChatBubbleProps {
  sender: 'ai' | 'user';
  content: string;
  time?: string;
  isStreaming?: boolean;
  /** When true, strips embedded JSON arrays and shows natural language only (workbench mode) */
  filterJson?: boolean;
}

export function ChatBubble({
  sender,
  content,
  time,
  isStreaming,
  filterJson = false,
}: ChatBubbleProps) {
  const isAI = sender === 'ai';

  function extractNaturalLanguage(
    text: string,
    streaming: boolean,
  ): { prose: string; caseCount: number } {
    let caseCount = 0;

    // 1. Remove complete fenced JSON code blocks
    let prose = text.replace(/```(?:json)?\s*([\s\S]*?)```/g, (_match, json) => {
      try {
        const parsed = JSON.parse(json.trim());
        if (Array.isArray(parsed)) {
          caseCount += parsed.length;
          return `\n\n{check} 已生成 ${parsed.length} 条测试用例，请查看右侧面板\n\n`;
        }
      } catch {
        // keep non-JSON code blocks
      }
      return '';
    });

    // 2. During streaming, also strip incomplete/unclosed code fences
    if (streaming) {
      // Remove everything from an unclosed ``` to end of string
      prose = prose.replace(/```[\s\S]*$/, '\n\n*正在生成测试用例...*');
    }

    // 3. Strip bare JSON arrays that aren't in code blocks (AI sometimes skips fences)
    prose = prose.replace(/(\[\s*\{[\s\S]*?\}\s*\])/g, (match) => {
      try {
        const parsed = JSON.parse(match);
        if (Array.isArray(parsed) && parsed.length > 0 && parsed[0]?.title) {
          caseCount += parsed.length;
          return `{check} 已生成 ${parsed.length} 条测试用例，请查看右侧面板`;
        }
      } catch {
        // keep
      }
      return '';
    });

    prose = prose.trim();
    return { prose, caseCount };
  }

  function renderMarkdown(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\{check\} (.+)/g, `<span style="color:var(--accent)">${CHECK_SVG} $1</span>`)
      .replace(/### (.+)/g, '<h3 style="font-size:13px;font-weight:700;margin:8px 0 4px">$1</h3>')
      .replace(/## (.+)/g, '<h2 style="font-size:14px;font-weight:700;margin:10px 0 4px">$1</h2>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(
        /`([^`]+)`/g,
        '<code style="background:rgba(0,0,0,0.3);padding:1px 4px;border-radius:3px;font-size:11px">$1</code>',
      )
      .replace(/^- (.+)$/gm, '<li style="margin-left:12px;list-style:disc">$1</li>')
      .replace(/^\d+\. (.+)$/gm, '<li style="margin-left:12px;list-style:decimal">$1</li>')
      .replace(/\n\n/g, '</p><p style="margin:6px 0">')
      .replace(/\n/g, '<br/>');
  }

  function renderAIContent(rawContent: string): string {
    if (!filterJson) {
      // In diagnosis/plain mode: render as markdown without stripping JSON
      return renderMarkdown(rawContent);
    }
    // Workbench mode: strip embedded JSON arrays, show only natural language
    const { prose } = extractNaturalLanguage(rawContent, isStreaming ?? false);

    if (!prose && isStreaming) {
      return '<span style="color:var(--text3)">正在生成测试用例...</span>';
    }
    if (!prose) {
      return `<span style="color:var(--accent)">${CHECK_SVG} 测试用例已生成，请查看右侧面板</span>`;
    }
    return renderMarkdown(prose);
  }

  return (
    <div className={`flex gap-2.5 mb-3.5 ${isAI ? '' : 'flex-row-reverse'}`}>
      <div
        className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-[12px] font-bold ${
          isAI
            ? 'bg-[linear-gradient(135deg,rgba(0,217,163,0.1),rgba(59,130,246,0.15))] border border-[rgba(0,217,163,0.3)] text-accent'
            : 'bg-bg3 border border-border text-text2'
        }`}
      >
        {isAI ? 'AI' : 'U'}
      </div>
      <div>
        <div
          className={`rounded-lg px-3 py-2.5 max-w-[480px] text-[12.5px] leading-relaxed ${
            isAI
              ? 'bg-[rgba(0,217,163,0.04)] border border-[rgba(0,217,163,0.2)] text-text'
              : 'bg-bg2 border border-border text-text'
          }`}
        >
          {isAI ? (
            // biome-ignore lint/security/noDangerouslySetInnerHtml: Markdown from trusted AI backend
            <div dangerouslySetInnerHTML={{ __html: renderAIContent(content) }} />
          ) : (
            content
          )}
          {isStreaming && (
            <span className="inline-block w-[2px] h-3 bg-accent ml-0.5 animate-[blink_1s_infinite]" />
          )}
        </div>
        {time && <div className="text-[10px] text-text3 mt-1 font-mono">{time}</div>}
      </div>
    </div>
  );
}
