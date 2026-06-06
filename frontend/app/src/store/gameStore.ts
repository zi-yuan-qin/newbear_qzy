import { create } from "zustand";
import { getCurrentUser, login, logout, register } from "../api/auth";
import {
  closeMeeting as closeMeetingApi,
  closeReport as closeReportApi,
  enterMeeting as enterMeetingApi,
  fetchWorldState,
  finishMeeting as finishMeetingApi,
  leavePantry as leavePantryApi,
  resetWorld,
  runStep,
  sendMeetingMessage as sendMeetingMessageApi,
  sendPantryMessage as sendPantryMessageApi,
  startMeeting as startMeetingApi,
  tickMeeting as tickMeetingApi,
  tickPantry as tickPantryApi,
} from "../api/game";
import type { AuthPayload, AuthUser, WorldState } from "../types/api";
type GameStore = {
  user: AuthUser | null;
  world: WorldState | null;
  status: string;
  isSubmitting: boolean;
  isBusy: boolean;
  checkAuth: () => Promise<void>;
  fetchWorld: () => Promise<void>;
  login: (payload: AuthPayload) => Promise<void>;
  register: (payload: AuthPayload) => Promise<void>;
  logout: () => Promise<void>;
  runStep: (affair: string) => Promise<void>;
  resetWorld: () => Promise<void>;
  enterMeeting: () => Promise<void>;
  startMeeting: () => Promise<void>;
  sendMeetingMessage: (message: string) => Promise<void>;
  tickMeeting: () => Promise<void>;
  finishMeeting: () => Promise<void>;
  closeMeeting: () => Promise<void>;
  sendPantryMessage: (message: string) => Promise<void>;
  tickPantry: () => Promise<void>;
  leavePantry: () => Promise<void>;
  closeReport: () => Promise<void>;
};
type WorldAction = () => Promise<{ state: WorldState }>;

async function runWorldAction(
  action: WorldAction,
  set: (partial: Partial<GameStore>) => void,
  pendingStatus: string,
  successStatus: string,
  failureStatus: string,
) {
  set({
    isBusy: true,
    status: pendingStatus,
  });

  try {
    const data = await action();

    set({
      world: data.state,
      status: successStatus,
    });
  } catch (error) {
    set({
      status: error instanceof Error ? error.message : failureStatus,
    });
  } finally {
    set({
      isBusy: false,
    });
  }
}

export const useGameStore = create<GameStore>((set) => ({
  user: null,
  world: null,
  status: "正在检查登录状态...",
  isSubmitting: false,
  isBusy: false,

  checkAuth: async () => {
  try {
    const data = await getCurrentUser();

    if (data.authenticated) {
      set({
        user: data.user,
        status: "已登录，正在读取世界状态...",
      });

      const worldData = await fetchWorldState();

      set({
        world: worldData.state,
        status: "已登录",
      });
    } else {
      set({
        user: null,
        world: null,
        status: "未登录",
      });
    }
  } catch (error) {
    set({
      status: error instanceof Error ? error.message : "接口请求失败",
    });
  }
},
  fetchWorld: async () => {
  try {
    const data = await fetchWorldState();

    set({
      world: data.state,
      status: "世界状态已更新",
    });
  } catch (error) {
    set({
      status: error instanceof Error ? error.message : "读取世界状态失败",
    });
  }
},

  login: async (payload) => {
    set({
      isSubmitting: true,
      status: "正在登录...",
    });

    try {
      const data = await login(payload);

      set({
        user: data.user,
        world: data.state,
        status: "登录成功",
      });
    } catch (error) {
      set({
        status: error instanceof Error ? error.message : "登录失败",
      });
    } finally {
      set({
        isSubmitting: false,
      });
    }
  },

  register: async (payload) => {
    set({
      isSubmitting: true,
      status: "正在注册...",
    });

    try {
      const data = await register(payload);

      set({
        user: data.user,
        world: data.state,
        status: "注册成功",
      });
    } catch (error) {
      set({
        status: error instanceof Error ? error.message : "注册失败",
      });
    } finally {
      set({
        isSubmitting: false,
      });
    }
  },

  logout: async () => {
    try {
      await logout();
    } finally {
      set({
        user: null,
        world: null,
        status: "已退出登录",
      });
    }
  },
  runStep: async (affair) => {
  set({
    isBusy: true,
    status: "正在推进时间...",
  });

  try {
    const data = await runStep({ affair });

    set({
      world: data.state,
      status: "时间已推进",
    });
  } catch (error) {
    set({
      status: error instanceof Error ? error.message : "推进失败",
    });
  } finally {
    set({
      isBusy: false,
    });
  }
},

resetWorld: async () => {
  set({
    isBusy: true,
    status: "正在重置世界...",
  });

  try {
    const data = await resetWorld();

    set({
      world: data.state,
      status: "世界已重置",
    });
  } catch (error) {
    set({
      status: error instanceof Error ? error.message : "重置失败",
    });
  } finally {
    set({
      isBusy: false,
    });
  }
},
enterMeeting: async () => {
  await runWorldAction(
    enterMeetingApi,
    set,
    "正在进入会议室...",
    "已进入会议室",
    "进入会议室失败",
  );
},

startMeeting: async () => {
  await runWorldAction(
    startMeetingApi,
    set,
    "正在开始会议...",
    "会议已开始",
    "开始会议失败",
  );
},

sendMeetingMessage: async (message) => {
  await runWorldAction(
    () => sendMeetingMessageApi(message),
    set,
    "正在发送会议发言...",
    "会议发言已发送",
    "发送会议发言失败",
  );
},

tickMeeting: async () => {
  await runWorldAction(
    tickMeetingApi,
    set,
    "正在推进会议...",
    "会议已推进",
    "推进会议失败",
  );
},

finishMeeting: async () => {
  await runWorldAction(
    finishMeetingApi,
    set,
    "正在结束会议...",
    "会议已结束",
    "结束会议失败",
  );
},

closeMeeting: async () => {
  await runWorldAction(
    closeMeetingApi,
    set,
    "正在关闭会议...",
    "已回到公司",
    "关闭会议失败",
  );
},

sendPantryMessage: async (message) => {
  await runWorldAction(
    () => sendPantryMessageApi(message),
    set,
    "正在发送茶水间发言...",
    "茶水间发言已发送",
    "发送茶水间发言失败",
  );
},

tickPantry: async () => {
  await runWorldAction(
    tickPantryApi,
    set,
    "正在推进茶水间对话...",
    "茶水间对话已推进",
    "推进茶水间失败",
  );
},

leavePantry: async () => {
  await runWorldAction(
    leavePantryApi,
    set,
    "正在离开茶水间...",
    "已离开茶水间",
    "离开茶水间失败",
  );
},

closeReport: async () => {
  await runWorldAction(
    closeReportApi,
    set,
    "正在关闭报告...",
    "已关闭报告",
    "关闭报告失败",
  );
},
}));
