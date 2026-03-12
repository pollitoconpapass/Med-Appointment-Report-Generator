import { useEffect, useRef } from "react";
import { Crepe } from "@milkdown/crepe";
import { replaceAll } from "@milkdown/utils";

export const MilkdownEditor = ({ content, onChange }) => {
  const containerRef = useRef(null);
  const crepeRef = useRef(null);

  // Initialize the editor once
  useEffect(() => {
    if (!containerRef.current || crepeRef.current) return;

    const crepe = new Crepe({
      root: containerRef.current,
      defaultValue: content,
      features: {
        [Crepe.Feature.BlockEdit]: false,
        [Crepe.Feature.Toolbar]: false,
        [Crepe.Feature.Slash]: false,
        [Crepe.Feature.ImageBlock]: false,
        [Crepe.Feature.Placeholder]: false,
        [Crepe.Feature.LinkTooltip]: false,
        [Crepe.Feature.TableBlock]: false,
      },
    });

    crepe.on((listener) => {
      listener.markdownUpdated((_, markdown) => {
        onChange(markdown);
      });
    });

    crepe.create().then(() => {
      crepeRef.current = crepe;
    });

    return () => {
      crepe.destroy();
      crepeRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Sync content changes from outside
  useEffect(() => {
    const crepe = crepeRef.current;
    if (!crepe) return;

    const current = crepe.getMarkdown();
    if (content !== current) {
      crepe.editor.action(replaceAll(content));
    }
  }, [content]);

  return <div ref={containerRef} />;
};
