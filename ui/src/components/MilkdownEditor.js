import { useEffect } from "react";
import { Milkdown, useEditor } from "@milkdown/react";
import { Crepe } from "@milkdown/crepe";

export const MilkdownEditor = ({ content, onChange }) => {
  const { get } = useEditor(
    (root) => {
      const crepe = new Crepe({
        root,
        defaultValue: content,
      });

      crepe.on((listener) => {
        listener.markdownUpdated((_, markdown) => {
          onChange(markdown);
        });
      });

      return crepe;
    },
    [onChange],
  );

  useEffect(() => {
    const editor = get();
    if (editor && content !== editor.getMarkdown()) {
      editor.setMarkdown(content);
    }
  }, [content, get]);

  return <Milkdown />;
};
