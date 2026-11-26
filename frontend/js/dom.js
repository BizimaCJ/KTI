// Tiny helper for building DOM safely. Text is always set with textContent, never innerHTML.
export function el(tag, options = {}, ...children) {
  const node = document.createElement(tag);
  if (options.className) node.className = options.className;
  if (options.text !== undefined) node.textContent = options.text;
  if (options.attrs) {
    for (const [key, value] of Object.entries(options.attrs)) node.setAttribute(key, value);
  }
  for (const child of children) {
    if (child) node.append(child);
  }
  return node;
}

export function clear(node) {
  node.replaceChildren();
}
