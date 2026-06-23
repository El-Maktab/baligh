import { Moon, Sun } from "lucide-react";
import { Button } from "react-aria-components";

import { useTheme, type ThemePreference } from "../../design-system";

const choices: Array<{
  value: ThemePreference;
  label: string;
  icon: typeof Sun;
}> = [
  { value: "light", label: "الوضع الفاتح", icon: Sun },
  { value: "dark", label: "الوضع الداكن", icon: Moon },
];

export function ThemeControl() {
  const { preference, setPreference } = useTheme();

  return (
    <div className="theme-control" aria-label="اختيار المظهر">
      {choices.map(({ value, label, icon: Icon }) => (
        <Button
          key={value}
          aria-label={label}
          className="theme-control__button"
          data-active={preference === value || undefined}
          onPress={() => setPreference(value)}
        >
          <Icon aria-hidden="true" size={18} strokeWidth={1.8} />
        </Button>
      ))}
    </div>
  );
}
