import type { AppComponent, AppPayload } from "../api/appApi";

export type AppComponentType = "button" | "card" | "custom" | "form" | "image" | "list" | "spacer" | "text";

export type AppComponentRegistryEntry = {
  binding: "action" | "data" | "form" | "none";
  component_type: AppComponentType;
  label: string;
  order: number;
  summary: string;
};

export type ComponentRegistryValidation = {
  duplicateTypes: AppComponentType[];
  isValid: boolean;
};

export type ComponentToolboxItem = AppComponentRegistryEntry & {
  count: number;
};

export const appComponentRegistry: AppComponentRegistryEntry[] = [
  {
    binding: "data",
    component_type: "text",
    label: "Text",
    order: 10,
    summary: "Display static or bound copy"
  },
  {
    binding: "action",
    component_type: "button",
    label: "Button",
    order: 20,
    summary: "Trigger a runtime action"
  },
  {
    binding: "form",
    component_type: "form",
    label: "Form",
    order: 30,
    summary: "Render a published form"
  },
  {
    binding: "data",
    component_type: "list",
    label: "List",
    order: 40,
    summary: "Render repeated records"
  },
  {
    binding: "none",
    component_type: "card",
    label: "Card",
    order: 50,
    summary: "Group related content"
  },
  {
    binding: "data",
    component_type: "image",
    label: "Image",
    order: 60,
    summary: "Render an image asset or URL"
  },
  {
    binding: "none",
    component_type: "spacer",
    label: "Spacer",
    order: 70,
    summary: "Control vertical rhythm"
  },
  {
    binding: "none",
    component_type: "custom",
    label: "Custom",
    order: 80,
    summary: "Module-provided component"
  }
];

export function getOrderedComponentRegistry(
  registry: AppComponentRegistryEntry[] = appComponentRegistry
): AppComponentRegistryEntry[] {
  return [...registry].sort((left, right) => left.order - right.order || left.label.localeCompare(right.label));
}

export function validateComponentRegistry(
  registry: AppComponentRegistryEntry[] = appComponentRegistry
): ComponentRegistryValidation {
  const duplicateTypes = findDuplicates(registry.map((entry) => entry.component_type));

  return {
    duplicateTypes,
    isValid: duplicateTypes.length === 0
  };
}

export function getComponentToolboxItems(payload: AppPayload | undefined): ComponentToolboxItem[] {
  const counts = new Map<AppComponentType, number>();

  for (const screen of payload?.screens ?? []) {
    for (const component of screen.components) {
      countComponentTree(component, counts);
    }
  }

  return getOrderedComponentRegistry().map((entry) => ({
    ...entry,
    count: counts.get(entry.component_type) ?? 0
  }));
}

function countComponentTree(component: AppComponent, counts: Map<AppComponentType, number>) {
  const componentType = component.component_type as AppComponentType;
  counts.set(componentType, (counts.get(componentType) ?? 0) + 1);
  for (const child of component.children ?? []) {
    countComponentTree(child, counts);
  }
}

function findDuplicates(values: AppComponentType[]): AppComponentType[] {
  const seen = new Set<AppComponentType>();
  const duplicates = new Set<AppComponentType>();

  for (const value of values) {
    if (seen.has(value)) {
      duplicates.add(value);
    }
    seen.add(value);
  }

  return [...duplicates].sort();
}
