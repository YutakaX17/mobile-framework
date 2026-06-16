import { describe, expect, it } from "vitest";

import {
  appComponentRegistry,
  getComponentToolboxItems,
  getOrderedComponentRegistry,
  validateComponentRegistry,
  type AppComponentRegistryEntry
} from "./appComponentRegistry";
import type { AppPayload } from "../api/appApi";

describe("app component registry", () => {
  it("keeps supported components in builder order", () => {
    expect(getOrderedComponentRegistry().map((entry) => entry.component_type)).toEqual([
      "text",
      "button",
      "form",
      "list",
      "card",
      "image",
      "spacer",
      "custom"
    ]);
  });

  it("validates the default registry", () => {
    expect(validateComponentRegistry()).toEqual({
      duplicateTypes: [],
      isValid: true
    });
  });

  it("detects duplicate component types", () => {
    const duplicate: AppComponentRegistryEntry = {
      ...appComponentRegistry[0],
      label: "Duplicate text"
    };

    expect(validateComponentRegistry([...appComponentRegistry, duplicate])).toEqual({
      duplicateTypes: ["text"],
      isValid: false
    });
  });

  it("counts component usage from an app payload", () => {
    const payload: AppPayload = {
      app_id: "field_ops_app",
      name: "Field Operations",
      navigation: [{ label: "Intake", screen_id: "intake" }],
      schema_version: "v1",
      screens: [
        {
          components: [
            {
              children: [
                {
                  component_id: "help_text",
                  component_type: "text"
                }
              ],
              component_id: "intake_card",
              component_type: "card"
            },
            {
              component_id: "intake_form",
              component_type: "form"
            }
          ],
          name: "Patient Intake",
          screen_id: "intake",
          screen_type: "form"
        }
      ],
      version: "0.1.0"
    };

    const counts = Object.fromEntries(getComponentToolboxItems(payload).map((item) => [item.component_type, item.count]));

    expect(counts).toMatchObject({
      card: 1,
      form: 1,
      text: 1
    });
  });
});
