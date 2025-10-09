\ Model Embalse_Nueva_Punilla_Multi
\ LP format - for model browsing. Use MPS format to capture full model detail.
\ Signature: 0x4246075e7c979c4d
Minimize
  d_A[0] + d_A[1] + d_A[2] + d_A[3] + d_A[4] + d_A[5] + d_A[6] + d_A[7]
   + d_A[8] + d_A[9] + d_A[10] + d_A[11] + d_B[0] + d_B[1] + d_B[2]
   + d_B[3] + d_B[4] + d_B[5] + d_B[6] + d_B[7] + d_B[8] + d_B[9] + d_B[10]
   + d_B[11]
Subject To
 lambda_sum: <= 0
 pref_eq_0: UPREF[0] = 7.9173504e+07
 sup_zero_0: SUP[0] = 0
 slpref_zero_0: SL_PREF[0] = 0
 pref_leq_Qin_0: UPREF[0] <= 7.9173504e+07
 rem_def_0: UPREF[0] + rem[0] = 7.9173504e+07
 capR_def_0: capR[0] = 1.75e+08
 capA_def_0: capA[0] = 2.6e+08
 capB_def_0: capB[0] = 1.05e+08
 tR_def_0: - rem[0] + capR[0] + tR[0] = 0
 fillR_def_0: - rem[0] + zR[0] + fillR[0] = 0
 invrfi_fillfirst_0: IN_VRFI[0] - fillR[0] = 0
 tAB_def_0: capA[0] + capB[0] - zR[0] + tAB[0] = 0
 EB_eq_0: EB[0] - EB_cap[0] = 0
 shareA_def_0: - 0.71 zR[0] + shareA[0] = 0
 shareB_def_0: - 0.29 zR[0] + shareB[0] = 0
 overflowA_def_0: - shareA[0] + yA[0] + overflowA[0] = 0
 overflowB_def_0: - shareB[0] + yB[0] + overflowB[0] = 0
 extraA_def_0: - capA[0] + yA[0] + extraA[0] = 0
 extraB_def_0: - capB[0] + yB[0] + extraB[0] = 0
 tA_leq_overflowB_0: - overflowB[0] + tA[0] <= 0
 tA_leq_extraA_0: - extraA[0] + tA[0] <= 0
 tB_leq_overflowA_0: - overflowA[0] + tB[0] <= 0
 tB_leq_extraB_0: - extraB[0] + tB[0] <= 0
 INA_final_0: INA[0] - yA[0] - tA[0] = 0
 INB_final_0: INB[0] - yB[0] - tB[0] = 0
 fill_AB_0: INA[0] + INB[0] + EB[0] - zR[0] = 0
 tA_tB_balance_0: EB[0] - zR[0] + yA[0] + yB[0] + tA[0] + tB[0] = 0
 L_R_cap_0: L_R[0] <= 0
 L_A_cap_0: L_A[0] <= 0
 L_B_cap_0: L_B[0] <= 0
 L_R_stockprev_0: L_R[0] <= 0
 L_A_stockprev_0: L_A[0] <= 0
 L_B_stockprev_0: L_B[0] <= 0
 def_deficit_A_0: R_A[0] + UVRFI_A[0] + d_A[0] = 1.06105e+07
 def_deficit_B_0: R_B[0] + UVRFI_B[0] + d_B[0] = 2.13e+06
 no_overserve_A_0: R_A[0] + UVRFI_A[0] <= 1.06105e+07
 no_overserve_B_0: R_B[0] + UVRFI_B[0] <= 2.13e+06
 Aempty_fix_0: A_empty[0] = 1
 Bempty_fix_0: B_empty[0] = 1
 tmp_vrfi_def_0: - IN_VRFI[0] + R_H[0] + tmp_vrfi[0] = 0
 auxA1_def_0: auxA1[0] = 5.30525e+06
 auxA2_def_0: - 0.71 VRFI_net[0] + auxA2[0] = 0
 auxB1_def_0: auxB1[0] = 1.065e+06
 auxB2_def_0: - 0.29 VRFI_net[0] + auxB2[0] = 0
 uvrfiA_min_lb_0: UVRFI_A[0] - 1.75e+08 A_empty[0] - minA_req[0]
   >= -1.75e+08
 uvrfiB_min_lb_0: UVRFI_B[0] - 1.75e+08 B_empty[0] - minB_req[0]
   >= -1.75e+08
 uvrfiA_cota_0: UVRFI_A[0] - 0.71 VRFI_net[0] <= 0
 uvrfiB_cota_0: UVRFI_B[0] - 0.29 VRFI_net[0] <= 0
 vrfi_avail_0: - IN_VRFI[0] + R_H[0] + UVRFI_A[0] + UVRFI_B[0] <= 0
 disp_A_0: - INA[0] + R_A[0] <= 0
 disp_B_0: - INB[0] + R_B[0] <= 0
 bal_R_0: V_R[0] - IN_VRFI[0] + R_H[0] + UVRFI_A[0] + UVRFI_B[0] + L_R[0]
   = 0
 bal_A_0: V_A[0] - INA[0] + R_A[0] + L_A[0] = 0
 bal_B_0: V_B[0] - INB[0] + R_B[0] + L_B[0] = 0
 qturb_0: - R_A[0] - R_B[0] - R_H[0] + 2.6784e+06 Q_turb[0] = 0
 pref_eq_1: UPREF[1] = 9.053856e+07
 sup_zero_1: SUP[1] = 0
 slpref_zero_1: SL_PREF[1] = 0
 pref_leq_Qin_1: UPREF[1] <= 9.053856e+07
 rem_def_1: UPREF[1] + rem[1] = 9.053856e+07
 capR_def_1: V_R[0] + capR[1] = 1.75e+08
 capA_def_1: V_A[0] + capA[1] = 2.6e+08
 capB_def_1: V_B[0] + capB[1] = 1.05e+08
 tR_def_1: - rem[1] + capR[1] + tR[1] = 0
 fillR_def_1: - rem[1] + zR[1] + fillR[1] = 0
 invrfi_fillfirst_1: IN_VRFI[1] - fillR[1] = 0
 tAB_def_1: capA[1] + capB[1] - zR[1] + tAB[1] = 0
 EB_eq_1: EB[1] - EB_cap[1] = 0
 shareA_def_1: - 0.71 zR[1] + shareA[1] = 0
 shareB_def_1: - 0.29 zR[1] + shareB[1] = 0
 overflowA_def_1: - shareA[1] + yA[1] + overflowA[1] = 0
 overflowB_def_1: - shareB[1] + yB[1] + overflowB[1] = 0
 extraA_def_1: - capA[1] + yA[1] + extraA[1] = 0
 extraB_def_1: - capB[1] + yB[1] + extraB[1] = 0
 tA_leq_overflowB_1: - overflowB[1] + tA[1] <= 0
 tA_leq_extraA_1: - extraA[1] + tA[1] <= 0
 tB_leq_overflowA_1: - overflowA[1] + tB[1] <= 0
 tB_leq_extraB_1: - extraB[1] + tB[1] <= 0
 INA_final_1: INA[1] - yA[1] - tA[1] = 0
 INB_final_1: INB[1] - yB[1] - tB[1] = 0
 fill_AB_1: INA[1] + INB[1] + EB[1] - zR[1] = 0
 tA_tB_balance_1: EB[1] - zR[1] + yA[1] + yB[1] + tA[1] + tB[1] = 0
 L_R_cap_1: L_R[1] <= 0
 L_A_cap_1: L_A[1] <= 0
 L_B_cap_1: L_B[1] <= 0
 L_R_stockprev_1: - V_R[0] + L_R[1] <= 0
 L_A_stockprev_1: - V_A[0] + L_A[1] <= 0
 L_B_stockprev_1: - V_B[0] + L_B[1] <= 0
 def_deficit_A_1: R_A[1] + UVRFI_A[1] + d_A[1] = 4.2442e+07
 def_deficit_B_1: R_B[1] + UVRFI_B[1] + d_B[1] = 1.065e+07
 no_overserve_A_1: R_A[1] + UVRFI_A[1] <= 4.2442e+07
 no_overserve_B_1: R_B[1] + UVRFI_B[1] <= 1.065e+07
 tmp_vrfi_def_1: - V_R[0] - IN_VRFI[1] + R_H[1] + tmp_vrfi[1] = 0
 auxA1_def_1: auxA1[1] = 2.1221e+07
 auxA2_def_1: - 0.71 VRFI_net[1] + auxA2[1] = 0
 auxB1_def_1: auxB1[1] = 5.325e+06
 auxB2_def_1: - 0.29 VRFI_net[1] + auxB2[1] = 0
 uvrfiA_min_lb_1: UVRFI_A[1] - 1.75e+08 A_empty[1] - minA_req[1]
   >= -1.75e+08
 uvrfiB_min_lb_1: UVRFI_B[1] - 1.75e+08 B_empty[1] - minB_req[1]
   >= -1.75e+08
 uvrfiA_cota_1: UVRFI_A[1] - 0.71 VRFI_net[1] <= 0
 uvrfiB_cota_1: UVRFI_B[1] - 0.29 VRFI_net[1] <= 0
 vrfi_avail_1: - V_R[0] - IN_VRFI[1] + R_H[1] + UVRFI_A[1] + UVRFI_B[1]
   <= 0
 disp_A_1: - V_A[0] - INA[1] + R_A[1] <= 0
 disp_B_1: - V_B[0] - INB[1] + R_B[1] <= 0
 bal_R_1: - V_R[0] + V_R[1] - IN_VRFI[1] + R_H[1] + UVRFI_A[1] + UVRFI_B[1]
   + L_R[1] = 0
 bal_A_1: - V_A[0] + V_A[1] - INA[1] + R_A[1] + L_A[1] = 0
 bal_B_1: - V_B[0] + V_B[1] - INB[1] + R_B[1] + L_B[1] = 0
 qturb_1: - R_A[1] - R_B[1] - R_H[1] + 2.592e+06 Q_turb[1] = 0
 pref_eq_2: UPREF[2] = 9.9154368000000015e+07
 sup_zero_2: SUP[2] = 0
 slpref_zero_2: SL_PREF[2] = 0
 pref_leq_Qin_2: UPREF[2] <= 9.9154368000000015e+07
 rem_def_2: UPREF[2] + rem[2] = 9.9154368000000015e+07
 capR_def_2: V_R[1] + capR[2] = 1.75e+08
 capA_def_2: V_A[1] + capA[2] = 2.6e+08
 capB_def_2: V_B[1] + capB[2] = 1.05e+08
 tR_def_2: - rem[2] + capR[2] + tR[2] = 0
 fillR_def_2: - rem[2] + zR[2] + fillR[2] = 0
 invrfi_fillfirst_2: IN_VRFI[2] - fillR[2] = 0
 tAB_def_2: capA[2] + capB[2] - zR[2] + tAB[2] = 0
 EB_eq_2: EB[2] - EB_cap[2] = 0
 shareA_def_2: - 0.71 zR[2] + shareA[2] = 0
 shareB_def_2: - 0.29 zR[2] + shareB[2] = 0
 overflowA_def_2: - shareA[2] + yA[2] + overflowA[2] = 0
 overflowB_def_2: - shareB[2] + yB[2] + overflowB[2] = 0
 extraA_def_2: - capA[2] + yA[2] + extraA[2] = 0
 extraB_def_2: - capB[2] + yB[2] + extraB[2] = 0
 tA_leq_overflowB_2: - overflowB[2] + tA[2] <= 0
 tA_leq_extraA_2: - extraA[2] + tA[2] <= 0
 tB_leq_overflowA_2: - overflowA[2] + tB[2] <= 0
 tB_leq_extraB_2: - extraB[2] + tB[2] <= 0
 INA_final_2: INA[2] - yA[2] - tA[2] = 0
 INB_final_2: INB[2] - yB[2] - tB[2] = 0
 fill_AB_2: INA[2] + INB[2] + EB[2] - zR[2] = 0
 tA_tB_balance_2: EB[2] - zR[2] + yA[2] + yB[2] + tA[2] + tB[2] = 0
 L_R_cap_2: L_R[2] <= 0
 L_A_cap_2: L_A[2] <= 0
 L_B_cap_2: L_B[2] <= 0
 L_R_stockprev_2: - V_R[1] + L_R[2] <= 0
 L_A_stockprev_2: - V_A[1] + L_A[2] <= 0
 L_B_stockprev_2: - V_B[1] + L_B[2] <= 0
 def_deficit_A_2: R_A[2] + UVRFI_A[2] + d_A[2] = 8.4884e+07
 def_deficit_B_2: R_B[2] + UVRFI_B[2] + d_B[2] = 2.13e+07
 no_overserve_A_2: R_A[2] + UVRFI_A[2] <= 8.4884e+07
 no_overserve_B_2: R_B[2] + UVRFI_B[2] <= 2.13e+07
 tmp_vrfi_def_2: - V_R[1] - IN_VRFI[2] + R_H[2] + tmp_vrfi[2] = 0
 auxA1_def_2: auxA1[2] = 4.2442e+07
 auxA2_def_2: - 0.71 VRFI_net[2] + auxA2[2] = 0
 auxB1_def_2: auxB1[2] = 1.065e+07
 auxB2_def_2: - 0.29 VRFI_net[2] + auxB2[2] = 0
 uvrfiA_min_lb_2: UVRFI_A[2] - 1.75e+08 A_empty[2] - minA_req[2]
   >= -1.75e+08
 uvrfiB_min_lb_2: UVRFI_B[2] - 1.75e+08 B_empty[2] - minB_req[2]
   >= -1.75e+08
 uvrfiA_cota_2: UVRFI_A[2] - 0.71 VRFI_net[2] <= 0
 uvrfiB_cota_2: UVRFI_B[2] - 0.29 VRFI_net[2] <= 0
 vrfi_avail_2: - V_R[1] - IN_VRFI[2] + R_H[2] + UVRFI_A[2] + UVRFI_B[2]
   <= 0
 disp_A_2: - V_A[1] - INA[2] + R_A[2] <= 0
 disp_B_2: - V_B[1] - INB[2] + R_B[2] <= 0
 bal_R_2: - V_R[1] + V_R[2] - IN_VRFI[2] + R_H[2] + UVRFI_A[2] + UVRFI_B[2]
   + L_R[2] = 0
 bal_A_2: - V_A[1] + V_A[2] - INA[2] + R_A[2] + L_A[2] = 0
 bal_B_2: - V_B[1] + V_B[2] - INB[2] + R_B[2] + L_B[2] = 0
 qturb_2: - R_A[2] - R_B[2] - R_H[2] + 2.6784e+06 Q_turb[2] = 0
 pref_eq_3: UPREF[3] = 7.584192e+07
 sup_zero_3: SUP[3] = 0
 slpref_zero_3: SL_PREF[3] = 0
 pref_leq_Qin_3: UPREF[3] <= 7.584192e+07
 rem_def_3: UPREF[3] + rem[3] = 7.584192e+07
 capR_def_3: V_R[2] + capR[3] = 1.75e+08
 capA_def_3: V_A[2] + capA[3] = 2.6e+08
 capB_def_3: V_B[2] + capB[3] = 1.05e+08
 tR_def_3: - rem[3] + capR[3] + tR[3] = 0
 fillR_def_3: - rem[3] + zR[3] + fillR[3] = 0
 invrfi_fillfirst_3: IN_VRFI[3] - fillR[3] = 0
 tAB_def_3: capA[3] + capB[3] - zR[3] + tAB[3] = 0
 EB_eq_3: EB[3] - EB_cap[3] = 0
 shareA_def_3: - 0.71 zR[3] + shareA[3] = 0
 shareB_def_3: - 0.29 zR[3] + shareB[3] = 0
 overflowA_def_3: - shareA[3] + yA[3] + overflowA[3] = 0
 overflowB_def_3: - shareB[3] + yB[3] + overflowB[3] = 0
 extraA_def_3: - capA[3] + yA[3] + extraA[3] = 0
 extraB_def_3: - capB[3] + yB[3] + extraB[3] = 0
 tA_leq_overflowB_3: - overflowB[3] + tA[3] <= 0
 tA_leq_extraA_3: - extraA[3] + tA[3] <= 0
 tB_leq_overflowA_3: - overflowA[3] + tB[3] <= 0
 tB_leq_extraB_3: - extraB[3] + tB[3] <= 0
 INA_final_3: INA[3] - yA[3] - tA[3] = 0
 INB_final_3: INB[3] - yB[3] - tB[3] = 0
 fill_AB_3: INA[3] + INB[3] + EB[3] - zR[3] = 0
 tA_tB_balance_3: EB[3] - zR[3] + yA[3] + yB[3] + tA[3] + tB[3] = 0
 L_R_cap_3: L_R[3] <= 0
 L_A_cap_3: L_A[3] <= 0
 L_B_cap_3: L_B[3] <= 0
 L_R_stockprev_3: - V_R[2] + L_R[3] <= 0
 L_A_stockprev_3: - V_A[2] + L_A[3] <= 0
 L_B_stockprev_3: - V_B[2] + L_B[3] <= 0
 def_deficit_A_3: R_A[3] + UVRFI_A[3] + d_A[3] = 1.27326e+08
 def_deficit_B_3: R_B[3] + UVRFI_B[3] + d_B[3] = 3.195e+07
 no_overserve_A_3: R_A[3] + UVRFI_A[3] <= 1.27326e+08
 no_overserve_B_3: R_B[3] + UVRFI_B[3] <= 3.195e+07
 tmp_vrfi_def_3: - V_R[2] - IN_VRFI[3] + R_H[3] + tmp_vrfi[3] = 0
 auxA1_def_3: auxA1[3] = 6.3663e+07
 auxA2_def_3: - 0.71 VRFI_net[3] + auxA2[3] = 0
 auxB1_def_3: auxB1[3] = 1.5975e+07
 auxB2_def_3: - 0.29 VRFI_net[3] + auxB2[3] = 0
 uvrfiA_min_lb_3: UVRFI_A[3] - 1.75e+08 A_empty[3] - minA_req[3]
   >= -1.75e+08
 uvrfiB_min_lb_3: UVRFI_B[3] - 1.75e+08 B_empty[3] - minB_req[3]
   >= -1.75e+08
 uvrfiA_cota_3: UVRFI_A[3] - 0.71 VRFI_net[3] <= 0
 uvrfiB_cota_3: UVRFI_B[3] - 0.29 VRFI_net[3] <= 0
 vrfi_avail_3: - V_R[2] - IN_VRFI[3] + R_H[3] + UVRFI_A[3] + UVRFI_B[3]
   <= 0
 disp_A_3: - V_A[2] - INA[3] + R_A[3] <= 0
 disp_B_3: - V_B[2] - INB[3] + R_B[3] <= 0
 bal_R_3: - V_R[2] + V_R[3] - IN_VRFI[3] + R_H[3] + UVRFI_A[3] + UVRFI_B[3]
   + L_R[3] = 0
 bal_A_3: - V_A[2] + V_A[3] - INA[3] + R_A[3] + L_A[3] = 0
 bal_B_3: - V_B[2] + V_B[3] - INB[3] + R_B[3] + L_B[3] = 0
 qturb_3: - R_A[3] - R_B[3] - R_H[3] + 2.592e+06 Q_turb[3] = 0
 pref_eq_4: UPREF[4] = 9.4842143999999985e+07
 sup_zero_4: SUP[4] = 0
 slpref_zero_4: SL_PREF[4] = 0
 pref_leq_Qin_4: UPREF[4] <= 9.4842143999999985e+07
 rem_def_4: UPREF[4] + rem[4] = 9.4842143999999985e+07
 capR_def_4: V_R[3] + capR[4] = 1.75e+08
 capA_def_4: V_A[3] + capA[4] = 2.6e+08
 capB_def_4: V_B[3] + capB[4] = 1.05e+08
 tR_def_4: - rem[4] + capR[4] + tR[4] = 0
 fillR_def_4: - rem[4] + zR[4] + fillR[4] = 0
 invrfi_fillfirst_4: IN_VRFI[4] - fillR[4] = 0
 tAB_def_4: capA[4] + capB[4] - zR[4] + tAB[4] = 0
 EB_eq_4: EB[4] - EB_cap[4] = 0
 shareA_def_4: - 0.71 zR[4] + shareA[4] = 0
 shareB_def_4: - 0.29 zR[4] + shareB[4] = 0
 overflowA_def_4: - shareA[4] + yA[4] + overflowA[4] = 0
 overflowB_def_4: - shareB[4] + yB[4] + overflowB[4] = 0
 extraA_def_4: - capA[4] + yA[4] + extraA[4] = 0
 extraB_def_4: - capB[4] + yB[4] + extraB[4] = 0
 tA_leq_overflowB_4: - overflowB[4] + tA[4] <= 0
 tA_leq_extraA_4: - extraA[4] + tA[4] <= 0
 tB_leq_overflowA_4: - overflowA[4] + tB[4] <= 0
 tB_leq_extraB_4: - extraB[4] + tB[4] <= 0
 INA_final_4: INA[4] - yA[4] - tA[4] = 0
 INB_final_4: INB[4] - yB[4] - tB[4] = 0
 fill_AB_4: INA[4] + INB[4] + EB[4] - zR[4] = 0
 tA_tB_balance_4: EB[4] - zR[4] + yA[4] + yB[4] + tA[4] + tB[4] = 0
 L_R_cap_4: L_R[4] <= 0
 L_A_cap_4: L_A[4] <= 0
 L_B_cap_4: L_B[4] <= 0
 L_R_stockprev_4: - V_R[3] + L_R[4] <= 0
 L_A_stockprev_4: - V_A[3] + L_A[4] <= 0
 L_B_stockprev_4: - V_B[3] + L_B[4] <= 0
 def_deficit_A_4: R_A[4] + UVRFI_A[4] + d_A[4] = 1.69768e+08
 def_deficit_B_4: R_B[4] + UVRFI_B[4] + d_B[4] = 4.26e+07
 no_overserve_A_4: R_A[4] + UVRFI_A[4] <= 1.69768e+08
 no_overserve_B_4: R_B[4] + UVRFI_B[4] <= 4.26e+07
 tmp_vrfi_def_4: - V_R[3] - IN_VRFI[4] + R_H[4] + tmp_vrfi[4] = 0
 auxA1_def_4: auxA1[4] = 8.4884e+07
 auxA2_def_4: - 0.71 VRFI_net[4] + auxA2[4] = 0
 auxB1_def_4: auxB1[4] = 2.13e+07
 auxB2_def_4: - 0.29 VRFI_net[4] + auxB2[4] = 0
 uvrfiA_min_lb_4: UVRFI_A[4] - 1.75e+08 A_empty[4] - minA_req[4]
   >= -1.75e+08
 uvrfiB_min_lb_4: UVRFI_B[4] - 1.75e+08 B_empty[4] - minB_req[4]
   >= -1.75e+08
 uvrfiA_cota_4: UVRFI_A[4] - 0.71 VRFI_net[4] <= 0
 uvrfiB_cota_4: UVRFI_B[4] - 0.29 VRFI_net[4] <= 0
 vrfi_avail_4: - V_R[3] - IN_VRFI[4] + R_H[4] + UVRFI_A[4] + UVRFI_B[4]
   <= 0
 disp_A_4: - V_A[3] - INA[4] + R_A[4] <= 0
 disp_B_4: - V_B[3] - INB[4] + R_B[4] <= 0
 bal_R_4: - V_R[3] + V_R[4] - IN_VRFI[4] + R_H[4] + UVRFI_A[4] + UVRFI_B[4]
   + L_R[4] = 0
 bal_A_4: - V_A[3] + V_A[4] - INA[4] + R_A[4] + L_A[4] = 0
 bal_B_4: - V_B[3] + V_B[4] - INB[4] + R_B[4] + L_B[4] = 0
 qturb_4: - R_A[4] - R_B[4] - R_H[4] + 2.6784e+06 Q_turb[4] = 0
 pref_eq_5: UPREF[5] = 1.045872e+08
 sup_zero_5: SUP[5] = 0
 slpref_zero_5: SL_PREF[5] = 0
 pref_leq_Qin_5: UPREF[5] <= 1.045872e+08
 rem_def_5: UPREF[5] + rem[5] = 1.045872e+08
 capR_def_5: V_R[4] + capR[5] = 1.75e+08
 capA_def_5: V_A[4] + capA[5] = 2.6e+08
 capB_def_5: V_B[4] + capB[5] = 1.05e+08
 tR_def_5: - rem[5] + capR[5] + tR[5] = 0
 fillR_def_5: - rem[5] + zR[5] + fillR[5] = 0
 invrfi_fillfirst_5: IN_VRFI[5] - fillR[5] = 0
 tAB_def_5: capA[5] + capB[5] - zR[5] + tAB[5] = 0
 EB_eq_5: EB[5] - EB_cap[5] = 0
 shareA_def_5: - 0.71 zR[5] + shareA[5] = 0
 shareB_def_5: - 0.29 zR[5] + shareB[5] = 0
 overflowA_def_5: - shareA[5] + yA[5] + overflowA[5] = 0
 overflowB_def_5: - shareB[5] + yB[5] + overflowB[5] = 0
 extraA_def_5: - capA[5] + yA[5] + extraA[5] = 0
 extraB_def_5: - capB[5] + yB[5] + extraB[5] = 0
 tA_leq_overflowB_5: - overflowB[5] + tA[5] <= 0
 tA_leq_extraA_5: - extraA[5] + tA[5] <= 0
 tB_leq_overflowA_5: - overflowA[5] + tB[5] <= 0
 tB_leq_extraB_5: - extraB[5] + tB[5] <= 0
 INA_final_5: INA[5] - yA[5] - tA[5] = 0
 INB_final_5: INB[5] - yB[5] - tB[5] = 0
 fill_AB_5: INA[5] + INB[5] + EB[5] - zR[5] = 0
 tA_tB_balance_5: EB[5] - zR[5] + yA[5] + yB[5] + tA[5] + tB[5] = 0
 L_R_cap_5: L_R[5] <= 0
 L_A_cap_5: L_A[5] <= 0
 L_B_cap_5: L_B[5] <= 0
 L_R_stockprev_5: - V_R[4] + L_R[5] <= 0
 L_A_stockprev_5: - V_A[4] + L_A[5] <= 0
 L_B_stockprev_5: - V_B[4] + L_B[5] <= 0
 def_deficit_A_5: R_A[5] + UVRFI_A[5] + d_A[5] = 1.27326e+08
 def_deficit_B_5: R_B[5] + UVRFI_B[5] + d_B[5] = 3.195e+07
 no_overserve_A_5: R_A[5] + UVRFI_A[5] <= 1.27326e+08
 no_overserve_B_5: R_B[5] + UVRFI_B[5] <= 3.195e+07
 tmp_vrfi_def_5: - V_R[4] - IN_VRFI[5] + R_H[5] + tmp_vrfi[5] = 0
 auxA1_def_5: auxA1[5] = 6.3663e+07
 auxA2_def_5: - 0.71 VRFI_net[5] + auxA2[5] = 0
 auxB1_def_5: auxB1[5] = 1.5975e+07
 auxB2_def_5: - 0.29 VRFI_net[5] + auxB2[5] = 0
 uvrfiA_min_lb_5: UVRFI_A[5] - 1.75e+08 A_empty[5] - minA_req[5]
   >= -1.75e+08
 uvrfiB_min_lb_5: UVRFI_B[5] - 1.75e+08 B_empty[5] - minB_req[5]
   >= -1.75e+08
 uvrfiA_cota_5: UVRFI_A[5] - 0.71 VRFI_net[5] <= 0
 uvrfiB_cota_5: UVRFI_B[5] - 0.29 VRFI_net[5] <= 0
 vrfi_avail_5: - V_R[4] - IN_VRFI[5] + R_H[5] + UVRFI_A[5] + UVRFI_B[5]
   <= 0
 disp_A_5: - V_A[4] - INA[5] + R_A[5] <= 0
 disp_B_5: - V_B[4] - INB[5] + R_B[5] <= 0
 bal_R_5: - V_R[4] + V_R[5] - IN_VRFI[5] + R_H[5] + UVRFI_A[5] + UVRFI_B[5]
   + L_R[5] = 0
 bal_A_5: - V_A[4] + V_A[5] - INA[5] + R_A[5] + L_A[5] = 0
 bal_B_5: - V_B[4] + V_B[5] - INB[5] + R_B[5] + L_B[5] = 0
 qturb_5: - R_A[5] - R_B[5] - R_H[5] + 2.592e+06 Q_turb[5] = 0
 pref_eq_6: UPREF[6] = 7.1084736e+07
 sup_zero_6: SUP[6] = 0
 slpref_zero_6: SL_PREF[6] = 0
 pref_leq_Qin_6: UPREF[6] <= 7.1084736e+07
 rem_def_6: UPREF[6] + rem[6] = 7.1084736e+07
 capR_def_6: V_R[5] + capR[6] = 1.75e+08
 capA_def_6: V_A[5] + capA[6] = 2.6e+08
 capB_def_6: V_B[5] + capB[6] = 1.05e+08
 tR_def_6: - rem[6] + capR[6] + tR[6] = 0
 fillR_def_6: - rem[6] + zR[6] + fillR[6] = 0
 invrfi_fillfirst_6: IN_VRFI[6] - fillR[6] = 0
 tAB_def_6: capA[6] + capB[6] - zR[6] + tAB[6] = 0
 EB_eq_6: EB[6] - EB_cap[6] = 0
 shareA_def_6: - 0.71 zR[6] + shareA[6] = 0
 shareB_def_6: - 0.29 zR[6] + shareB[6] = 0
 overflowA_def_6: - shareA[6] + yA[6] + overflowA[6] = 0
 overflowB_def_6: - shareB[6] + yB[6] + overflowB[6] = 0
 extraA_def_6: - capA[6] + yA[6] + extraA[6] = 0
 extraB_def_6: - capB[6] + yB[6] + extraB[6] = 0
 tA_leq_overflowB_6: - overflowB[6] + tA[6] <= 0
 tA_leq_extraA_6: - extraA[6] + tA[6] <= 0
 tB_leq_overflowA_6: - overflowA[6] + tB[6] <= 0
 tB_leq_extraB_6: - extraB[6] + tB[6] <= 0
 INA_final_6: INA[6] - yA[6] - tA[6] = 0
 INB_final_6: INB[6] - yB[6] - tB[6] = 0
 fill_AB_6: INA[6] + INB[6] + EB[6] - zR[6] = 0
 tA_tB_balance_6: EB[6] - zR[6] + yA[6] + yB[6] + tA[6] + tB[6] = 0
 L_R_cap_6: L_R[6] <= 0
 L_A_cap_6: L_A[6] <= 0
 L_B_cap_6: L_B[6] <= 0
 L_R_stockprev_6: - V_R[5] + L_R[6] <= 0
 L_A_stockprev_6: - V_A[5] + L_A[6] <= 0
 L_B_stockprev_6: - V_B[5] + L_B[6] <= 0
 def_deficit_A_6: R_A[6] + UVRFI_A[6] + d_A[6] = 8.4884e+07
 def_deficit_B_6: R_B[6] + UVRFI_B[6] + d_B[6] = 2.13e+07
 no_overserve_A_6: R_A[6] + UVRFI_A[6] <= 8.4884e+07
 no_overserve_B_6: R_B[6] + UVRFI_B[6] <= 2.13e+07
 tmp_vrfi_def_6: - V_R[5] - IN_VRFI[6] + R_H[6] + tmp_vrfi[6] = 0
 auxA1_def_6: auxA1[6] = 4.2442e+07
 auxA2_def_6: - 0.71 VRFI_net[6] + auxA2[6] = 0
 auxB1_def_6: auxB1[6] = 1.065e+07
 auxB2_def_6: - 0.29 VRFI_net[6] + auxB2[6] = 0
 uvrfiA_min_lb_6: UVRFI_A[6] - 1.75e+08 A_empty[6] - minA_req[6]
   >= -1.75e+08
 uvrfiB_min_lb_6: UVRFI_B[6] - 1.75e+08 B_empty[6] - minB_req[6]
   >= -1.75e+08
 uvrfiA_cota_6: UVRFI_A[6] - 0.71 VRFI_net[6] <= 0
 uvrfiB_cota_6: UVRFI_B[6] - 0.29 VRFI_net[6] <= 0
 vrfi_avail_6: - V_R[5] - IN_VRFI[6] + R_H[6] + UVRFI_A[6] + UVRFI_B[6]
   <= 0
 disp_A_6: - V_A[5] - INA[6] + R_A[6] <= 0
 disp_B_6: - V_B[5] - INB[6] + R_B[6] <= 0
 bal_R_6: - V_R[5] + V_R[6] - IN_VRFI[6] + R_H[6] + UVRFI_A[6] + UVRFI_B[6]
   + L_R[6] = 0
 bal_A_6: - V_A[5] + V_A[6] - INA[6] + R_A[6] + L_A[6] = 0
 bal_B_6: - V_B[5] + V_B[6] - INB[6] + R_B[6] + L_B[6] = 0
 qturb_6: - R_A[6] - R_B[6] - R_H[6] + 2.6784e+06 Q_turb[6] = 0
 pref_eq_7: UPREF[7] = 6.97248e+07
 sup_zero_7: SUP[7] = 0
 slpref_zero_7: SL_PREF[7] = 0
 pref_leq_Qin_7: UPREF[7] <= 6.97248e+07
 rem_def_7: UPREF[7] + rem[7] = 6.97248e+07
 capR_def_7: V_R[6] + capR[7] = 1.75e+08
 capA_def_7: V_A[6] + capA[7] = 2.6e+08
 capB_def_7: V_B[6] + capB[7] = 1.05e+08
 tR_def_7: - rem[7] + capR[7] + tR[7] = 0
 fillR_def_7: - rem[7] + zR[7] + fillR[7] = 0
 invrfi_fillfirst_7: IN_VRFI[7] - fillR[7] = 0
 tAB_def_7: capA[7] + capB[7] - zR[7] + tAB[7] = 0
 EB_eq_7: EB[7] - EB_cap[7] = 0
 shareA_def_7: - 0.71 zR[7] + shareA[7] = 0
 shareB_def_7: - 0.29 zR[7] + shareB[7] = 0
 overflowA_def_7: - shareA[7] + yA[7] + overflowA[7] = 0
 overflowB_def_7: - shareB[7] + yB[7] + overflowB[7] = 0
 extraA_def_7: - capA[7] + yA[7] + extraA[7] = 0
 extraB_def_7: - capB[7] + yB[7] + extraB[7] = 0
 tA_leq_overflowB_7: - overflowB[7] + tA[7] <= 0
 tA_leq_extraA_7: - extraA[7] + tA[7] <= 0
 tB_leq_overflowA_7: - overflowA[7] + tB[7] <= 0
 tB_leq_extraB_7: - extraB[7] + tB[7] <= 0
 INA_final_7: INA[7] - yA[7] - tA[7] = 0
 INB_final_7: INB[7] - yB[7] - tB[7] = 0
 fill_AB_7: INA[7] + INB[7] + EB[7] - zR[7] = 0
 tA_tB_balance_7: EB[7] - zR[7] + yA[7] + yB[7] + tA[7] + tB[7] = 0
 L_R_cap_7: L_R[7] <= 0
 L_A_cap_7: L_A[7] <= 0
 L_B_cap_7: L_B[7] <= 0
 L_R_stockprev_7: - V_R[6] + L_R[7] <= 0
 L_A_stockprev_7: - V_A[6] + L_A[7] <= 0
 L_B_stockprev_7: - V_B[6] + L_B[7] <= 0
 def_deficit_A_7: R_A[7] + UVRFI_A[7] + d_A[7] = 4.2442e+07
 def_deficit_B_7: R_B[7] + UVRFI_B[7] + d_B[7] = 1.065e+07
 no_overserve_A_7: R_A[7] + UVRFI_A[7] <= 4.2442e+07
 no_overserve_B_7: R_B[7] + UVRFI_B[7] <= 1.065e+07
 tmp_vrfi_def_7: - V_R[6] - IN_VRFI[7] + R_H[7] + tmp_vrfi[7] = 0
 auxA1_def_7: auxA1[7] = 2.1221e+07
 auxA2_def_7: - 0.71 VRFI_net[7] + auxA2[7] = 0
 auxB1_def_7: auxB1[7] = 5.325e+06
 auxB2_def_7: - 0.29 VRFI_net[7] + auxB2[7] = 0
 uvrfiA_min_lb_7: UVRFI_A[7] - 1.75e+08 A_empty[7] - minA_req[7]
   >= -1.75e+08
 uvrfiB_min_lb_7: UVRFI_B[7] - 1.75e+08 B_empty[7] - minB_req[7]
   >= -1.75e+08
 uvrfiA_cota_7: UVRFI_A[7] - 0.71 VRFI_net[7] <= 0
 uvrfiB_cota_7: UVRFI_B[7] - 0.29 VRFI_net[7] <= 0
 vrfi_avail_7: - V_R[6] - IN_VRFI[7] + R_H[7] + UVRFI_A[7] + UVRFI_B[7]
   <= 0
 disp_A_7: - V_A[6] - INA[7] + R_A[7] <= 0
 disp_B_7: - V_B[6] - INB[7] + R_B[7] <= 0
 bal_R_7: - V_R[6] + V_R[7] - IN_VRFI[7] + R_H[7] + UVRFI_A[7] + UVRFI_B[7]
   + L_R[7] = 0
 bal_A_7: - V_A[6] + V_A[7] - INA[7] + R_A[7] + L_A[7] = 0
 bal_B_7: - V_B[6] + V_B[7] - INB[7] + R_B[7] + L_B[7] = 0
 qturb_7: - R_A[7] - R_B[7] - R_H[7] + 2.592e+06 Q_turb[7] = 0
 pref_eq_8: UPREF[8] = 5.7987359999999993e+07
 sup_zero_8: SUP[8] = 0
 slpref_zero_8: SL_PREF[8] = 0
 pref_leq_Qin_8: UPREF[8] <= 5.7987359999999993e+07
 rem_def_8: UPREF[8] + rem[8] = 5.7987359999999993e+07
 capR_def_8: V_R[7] + capR[8] = 1.75e+08
 capA_def_8: V_A[7] + capA[8] = 2.6e+08
 capB_def_8: V_B[7] + capB[8] = 1.05e+08
 tR_def_8: - rem[8] + capR[8] + tR[8] = 0
 fillR_def_8: - rem[8] + zR[8] + fillR[8] = 0
 invrfi_fillfirst_8: IN_VRFI[8] - fillR[8] = 0
 tAB_def_8: capA[8] + capB[8] - zR[8] + tAB[8] = 0
 EB_eq_8: EB[8] - EB_cap[8] = 0
 shareA_def_8: - 0.71 zR[8] + shareA[8] = 0
 shareB_def_8: - 0.29 zR[8] + shareB[8] = 0
 overflowA_def_8: - shareA[8] + yA[8] + overflowA[8] = 0
 overflowB_def_8: - shareB[8] + yB[8] + overflowB[8] = 0
 extraA_def_8: - capA[8] + yA[8] + extraA[8] = 0
 extraB_def_8: - capB[8] + yB[8] + extraB[8] = 0
 tA_leq_overflowB_8: - overflowB[8] + tA[8] <= 0
 tA_leq_extraA_8: - extraA[8] + tA[8] <= 0
 tB_leq_overflowA_8: - overflowA[8] + tB[8] <= 0
 tB_leq_extraB_8: - extraB[8] + tB[8] <= 0
 INA_final_8: INA[8] - yA[8] - tA[8] = 0
 INB_final_8: INB[8] - yB[8] - tB[8] = 0
 fill_AB_8: INA[8] + INB[8] + EB[8] - zR[8] = 0
 tA_tB_balance_8: EB[8] - zR[8] + yA[8] + yB[8] + tA[8] + tB[8] = 0
 L_R_cap_8: L_R[8] <= 0
 L_A_cap_8: L_A[8] <= 0
 L_B_cap_8: L_B[8] <= 0
 L_R_stockprev_8: - V_R[7] + L_R[8] <= 0
 L_A_stockprev_8: - V_A[7] + L_A[8] <= 0
 L_B_stockprev_8: - V_B[7] + L_B[8] <= 0
 def_deficit_A_8: R_A[8] + UVRFI_A[8] + d_A[8] = 1.06105e+07
 def_deficit_B_8: R_B[8] + UVRFI_B[8] + d_B[8] = 2.13e+06
 no_overserve_A_8: R_A[8] + UVRFI_A[8] <= 1.06105e+07
 no_overserve_B_8: R_B[8] + UVRFI_B[8] <= 2.13e+06
 tmp_vrfi_def_8: - V_R[7] - IN_VRFI[8] + R_H[8] + tmp_vrfi[8] = 0
 auxA1_def_8: auxA1[8] = 5.30525e+06
 auxA2_def_8: - 0.71 VRFI_net[8] + auxA2[8] = 0
 auxB1_def_8: auxB1[8] = 1.065e+06
 auxB2_def_8: - 0.29 VRFI_net[8] + auxB2[8] = 0
 uvrfiA_min_lb_8: UVRFI_A[8] - 1.75e+08 A_empty[8] - minA_req[8]
   >= -1.75e+08
 uvrfiB_min_lb_8: UVRFI_B[8] - 1.75e+08 B_empty[8] - minB_req[8]
   >= -1.75e+08
 uvrfiA_cota_8: UVRFI_A[8] - 0.71 VRFI_net[8] <= 0
 uvrfiB_cota_8: UVRFI_B[8] - 0.29 VRFI_net[8] <= 0
 vrfi_avail_8: - V_R[7] - IN_VRFI[8] + R_H[8] + UVRFI_A[8] + UVRFI_B[8]
   <= 0
 disp_A_8: - V_A[7] - INA[8] + R_A[8] <= 0
 disp_B_8: - V_B[7] - INB[8] + R_B[8] <= 0
 bal_R_8: - V_R[7] + V_R[8] - IN_VRFI[8] + R_H[8] + UVRFI_A[8] + UVRFI_B[8]
   + L_R[8] = 0
 bal_A_8: - V_A[7] + V_A[8] - INA[8] + R_A[8] + L_A[8] = 0
 bal_B_8: - V_B[7] + V_B[8] - INB[8] + R_B[8] + L_B[8] = 0
 qturb_8: - R_A[8] - R_B[8] - R_H[8] + 2.6784e+06 Q_turb[8] = 0
 pref_eq_9: UPREF[9] = 4.828896e+07
 sup_zero_9: SUP[9] = 0
 slpref_zero_9: SL_PREF[9] = 0
 pref_leq_Qin_9: UPREF[9] <= 4.828896e+07
 rem_def_9: UPREF[9] + rem[9] = 4.828896e+07
 capR_def_9: V_R[8] + capR[9] = 1.75e+08
 capA_def_9: V_A[8] + capA[9] = 2.6e+08
 capB_def_9: V_B[8] + capB[9] = 1.05e+08
 tR_def_9: - rem[9] + capR[9] + tR[9] = 0
 fillR_def_9: - rem[9] + zR[9] + fillR[9] = 0
 invrfi_fillfirst_9: IN_VRFI[9] - fillR[9] = 0
 tAB_def_9: capA[9] + capB[9] - zR[9] + tAB[9] = 0
 EB_eq_9: EB[9] - EB_cap[9] = 0
 shareA_def_9: - 0.71 zR[9] + shareA[9] = 0
 shareB_def_9: - 0.29 zR[9] + shareB[9] = 0
 overflowA_def_9: - shareA[9] + yA[9] + overflowA[9] = 0
 overflowB_def_9: - shareB[9] + yB[9] + overflowB[9] = 0
 extraA_def_9: - capA[9] + yA[9] + extraA[9] = 0
 extraB_def_9: - capB[9] + yB[9] + extraB[9] = 0
 tA_leq_overflowB_9: - overflowB[9] + tA[9] <= 0
 tA_leq_extraA_9: - extraA[9] + tA[9] <= 0
 tB_leq_overflowA_9: - overflowA[9] + tB[9] <= 0
 tB_leq_extraB_9: - extraB[9] + tB[9] <= 0
 INA_final_9: INA[9] - yA[9] - tA[9] = 0
 INB_final_9: INB[9] - yB[9] - tB[9] = 0
 fill_AB_9: INA[9] + INB[9] + EB[9] - zR[9] = 0
 tA_tB_balance_9: EB[9] - zR[9] + yA[9] + yB[9] + tA[9] + tB[9] = 0
 L_R_cap_9: L_R[9] <= 0
 L_A_cap_9: L_A[9] <= 0
 L_B_cap_9: L_B[9] <= 0
 L_R_stockprev_9: - V_R[8] + L_R[9] <= 0
 L_A_stockprev_9: - V_A[8] + L_A[9] <= 0
 L_B_stockprev_9: - V_B[8] + L_B[9] <= 0
 def_deficit_A_9: R_A[9] + UVRFI_A[9] + d_A[9] = 0
 def_deficit_B_9: R_B[9] + UVRFI_B[9] + d_B[9] = 0
 no_overserve_A_9: R_A[9] + UVRFI_A[9] <= 0
 no_overserve_B_9: R_B[9] + UVRFI_B[9] <= 0
 tmp_vrfi_def_9: - V_R[8] - IN_VRFI[9] + R_H[9] + tmp_vrfi[9] = 0
 auxA1_def_9: auxA1[9] = 0
 auxA2_def_9: - 0.71 VRFI_net[9] + auxA2[9] = 0
 auxB1_def_9: auxB1[9] = 0
 auxB2_def_9: - 0.29 VRFI_net[9] + auxB2[9] = 0
 uvrfiA_min_lb_9: UVRFI_A[9] - 1.75e+08 A_empty[9] - minA_req[9]
   >= -1.75e+08
 uvrfiB_min_lb_9: UVRFI_B[9] - 1.75e+08 B_empty[9] - minB_req[9]
   >= -1.75e+08
 uvrfiA_cota_9: UVRFI_A[9] - 0.71 VRFI_net[9] <= 0
 uvrfiB_cota_9: UVRFI_B[9] - 0.29 VRFI_net[9] <= 0
 vrfi_avail_9: - V_R[8] - IN_VRFI[9] + R_H[9] + UVRFI_A[9] + UVRFI_B[9]
   <= 0
 disp_A_9: - V_A[8] - INA[9] + R_A[9] <= 0
 disp_B_9: - V_B[8] - INB[9] + R_B[9] <= 0
 bal_R_9: - V_R[8] + V_R[9] - IN_VRFI[9] + R_H[9] + UVRFI_A[9] + UVRFI_B[9]
   + L_R[9] = 0
 bal_A_9: - V_A[8] + V_A[9] - INA[9] + R_A[9] + L_A[9] = 0
 bal_B_9: - V_B[8] + V_B[9] - INB[9] + R_B[9] + L_B[9] = 0
 qturb_9: - R_A[9] - R_B[9] - R_H[9] + 2.592e+06 Q_turb[9] = 0
 pref_eq_10: UPREF[10] = 2.1534335999999996e+07
 sup_zero_10: SUP[10] = 0
 slpref_zero_10: SL_PREF[10] = 0
 pref_leq_Qin_10: UPREF[10] <= 2.1534335999999996e+07
 rem_def_10: UPREF[10] + rem[10] = 2.1534335999999996e+07
 capR_def_10: V_R[9] + capR[10] = 1.75e+08
 capA_def_10: V_A[9] + capA[10] = 2.6e+08
 capB_def_10: V_B[9] + capB[10] = 1.05e+08
 tR_def_10: - rem[10] + capR[10] + tR[10] = 0
 fillR_def_10: - rem[10] + zR[10] + fillR[10] = 0
 invrfi_fillfirst_10: IN_VRFI[10] - fillR[10] = 0
 tAB_def_10: capA[10] + capB[10] - zR[10] + tAB[10] = 0
 EB_eq_10: EB[10] - EB_cap[10] = 0
 shareA_def_10: - 0.71 zR[10] + shareA[10] = 0
 shareB_def_10: - 0.29 zR[10] + shareB[10] = 0
 overflowA_def_10: - shareA[10] + yA[10] + overflowA[10] = 0
 overflowB_def_10: - shareB[10] + yB[10] + overflowB[10] = 0
 extraA_def_10: - capA[10] + yA[10] + extraA[10] = 0
 extraB_def_10: - capB[10] + yB[10] + extraB[10] = 0
 tA_leq_overflowB_10: - overflowB[10] + tA[10] <= 0
 tA_leq_extraA_10: - extraA[10] + tA[10] <= 0
 tB_leq_overflowA_10: - overflowA[10] + tB[10] <= 0
 tB_leq_extraB_10: - extraB[10] + tB[10] <= 0
 INA_final_10: INA[10] - yA[10] - tA[10] = 0
 INB_final_10: INB[10] - yB[10] - tB[10] = 0
 fill_AB_10: INA[10] + INB[10] + EB[10] - zR[10] = 0
 tA_tB_balance_10: EB[10] - zR[10] + yA[10] + yB[10] + tA[10] + tB[10] = 0
 L_R_cap_10: L_R[10] <= 0
 L_A_cap_10: L_A[10] <= 0
 L_B_cap_10: L_B[10] <= 0
 L_R_stockprev_10: - V_R[9] + L_R[10] <= 0
 L_A_stockprev_10: - V_A[9] + L_A[10] <= 0
 L_B_stockprev_10: - V_B[9] + L_B[10] <= 0
 def_deficit_A_10: R_A[10] + UVRFI_A[10] + d_A[10] = 0
 def_deficit_B_10: R_B[10] + UVRFI_B[10] + d_B[10] = 0
 no_overserve_A_10: R_A[10] + UVRFI_A[10] <= 0
 no_overserve_B_10: R_B[10] + UVRFI_B[10] <= 0
 tmp_vrfi_def_10: - V_R[9] - IN_VRFI[10] + R_H[10] + tmp_vrfi[10] = 0
 auxA1_def_10: auxA1[10] = 0
 auxA2_def_10: - 0.71 VRFI_net[10] + auxA2[10] = 0
 auxB1_def_10: auxB1[10] = 0
 auxB2_def_10: - 0.29 VRFI_net[10] + auxB2[10] = 0
 uvrfiA_min_lb_10: UVRFI_A[10] - 1.75e+08 A_empty[10] - minA_req[10]
   >= -1.75e+08
 uvrfiB_min_lb_10: UVRFI_B[10] - 1.75e+08 B_empty[10] - minB_req[10]
   >= -1.75e+08
 uvrfiA_cota_10: UVRFI_A[10] - 0.71 VRFI_net[10] <= 0
 uvrfiB_cota_10: UVRFI_B[10] - 0.29 VRFI_net[10] <= 0
 vrfi_avail_10: - V_R[9] - IN_VRFI[10] + R_H[10] + UVRFI_A[10]
   + UVRFI_B[10] <= 0
 disp_A_10: - V_A[9] - INA[10] + R_A[10] <= 0
 disp_B_10: - V_B[9] - INB[10] + R_B[10] <= 0
 bal_R_10: - V_R[9] + V_R[10] - IN_VRFI[10] + R_H[10] + UVRFI_A[10]
   + UVRFI_B[10] + L_R[10] = 0
 bal_A_10: - V_A[9] + V_A[10] - INA[10] + R_A[10] + L_A[10] = 0
 bal_B_10: - V_B[9] + V_B[10] - INB[10] + R_B[10] + L_B[10] = 0
 qturb_10: - R_A[10] - R_B[10] - R_H[10] + 2.6784e+06 Q_turb[10] = 0
 pref_eq_11: UPREF[11] = 2.115072e+07
 sup_zero_11: SUP[11] = 0
 slpref_zero_11: SL_PREF[11] = 0
 pref_leq_Qin_11: UPREF[11] <= 2.115072e+07
 rem_def_11: UPREF[11] + rem[11] = 2.115072e+07
 capR_def_11: V_R[10] + capR[11] = 1.75e+08
 capA_def_11: V_A[10] + capA[11] = 2.6e+08
 capB_def_11: V_B[10] + capB[11] = 1.05e+08
 tR_def_11: - rem[11] + capR[11] + tR[11] = 0
 fillR_def_11: - rem[11] + zR[11] + fillR[11] = 0
 invrfi_fillfirst_11: IN_VRFI[11] - fillR[11] = 0
 tAB_def_11: capA[11] + capB[11] - zR[11] + tAB[11] = 0
 EB_eq_11: EB[11] - EB_cap[11] = 0
 shareA_def_11: - 0.71 zR[11] + shareA[11] = 0
 shareB_def_11: - 0.29 zR[11] + shareB[11] = 0
 overflowA_def_11: - shareA[11] + yA[11] + overflowA[11] = 0
 overflowB_def_11: - shareB[11] + yB[11] + overflowB[11] = 0
 extraA_def_11: - capA[11] + yA[11] + extraA[11] = 0
 extraB_def_11: - capB[11] + yB[11] + extraB[11] = 0
 tA_leq_overflowB_11: - overflowB[11] + tA[11] <= 0
 tA_leq_extraA_11: - extraA[11] + tA[11] <= 0
 tB_leq_overflowA_11: - overflowA[11] + tB[11] <= 0
 tB_leq_extraB_11: - extraB[11] + tB[11] <= 0
 INA_final_11: INA[11] - yA[11] - tA[11] = 0
 INB_final_11: INB[11] - yB[11] - tB[11] = 0
 fill_AB_11: INA[11] + INB[11] + EB[11] - zR[11] = 0
 tA_tB_balance_11: EB[11] - zR[11] + yA[11] + yB[11] + tA[11] + tB[11] = 0
 L_R_cap_11: L_R[11] <= 0
 L_A_cap_11: L_A[11] <= 0
 L_B_cap_11: L_B[11] <= 0
 L_R_stockprev_11: - V_R[10] + L_R[11] <= 0
 L_A_stockprev_11: - V_A[10] + L_A[11] <= 0
 L_B_stockprev_11: - V_B[10] + L_B[11] <= 0
 def_deficit_A_11: R_A[11] + UVRFI_A[11] + d_A[11] = 0
 def_deficit_B_11: R_B[11] + UVRFI_B[11] + d_B[11] = 0
 no_overserve_A_11: R_A[11] + UVRFI_A[11] <= 0
 no_overserve_B_11: R_B[11] + UVRFI_B[11] <= 0
 tmp_vrfi_def_11: - V_R[10] - IN_VRFI[11] + R_H[11] + tmp_vrfi[11] = 0
 auxA1_def_11: auxA1[11] = 0
 auxA2_def_11: - 0.71 VRFI_net[11] + auxA2[11] = 0
 auxB1_def_11: auxB1[11] = 0
 auxB2_def_11: - 0.29 VRFI_net[11] + auxB2[11] = 0
 uvrfiA_min_lb_11: UVRFI_A[11] - 1.75e+08 A_empty[11] - minA_req[11]
   >= -1.75e+08
 uvrfiB_min_lb_11: UVRFI_B[11] - 1.75e+08 B_empty[11] - minB_req[11]
   >= -1.75e+08
 uvrfiA_cota_11: UVRFI_A[11] - 0.71 VRFI_net[11] <= 0
 uvrfiB_cota_11: UVRFI_B[11] - 0.29 VRFI_net[11] <= 0
 vrfi_avail_11: - V_R[10] - IN_VRFI[11] + R_H[11] + UVRFI_A[11]
   + UVRFI_B[11] <= 0
 disp_A_11: - V_A[10] - INA[11] + R_A[11] <= 0
 disp_B_11: - V_B[10] - INB[11] + R_B[11] <= 0
 bal_R_11: - V_R[10] + V_R[11] - IN_VRFI[11] + R_H[11] + UVRFI_A[11]
   + UVRFI_B[11] + L_R[11] = 0
 bal_A_11: - V_A[10] + V_A[11] - INA[11] + R_A[11] + L_A[11] = 0
 bal_B_11: - V_B[10] + V_B[11] - INB[11] + R_B[11] + L_B[11] = 0
 qturb_11: - R_A[11] - R_B[11] - R_H[11] + 2.592e+06 Q_turb[11] = 0
 humano_anual_y0: R_H[0] + R_H[1] + R_H[2] + R_H[3] + R_H[4] + R_H[5]
   + R_H[6] + R_H[7] + R_H[8] + R_H[9] + R_H[10] + R_H[11] = 3.9e+06
 uvrfiA_half_dem_if_empty_0: A_empty[0] = 1 -> UVRFI_A[0] <= 5.30525e+06
 uvrfiB_half_dem_if_empty_0: B_empty[0] = 1 -> UVRFI_B[0] <= 1.065e+06
 Aempty1_1: A_empty[1] = 1 -> V_A[0] <= 1
 Aempty0_1: A_empty[1] = 0 -> V_A[0] >= 1
 Bempty1_1: B_empty[1] = 1 -> V_B[0] <= 1
 Bempty0_1: B_empty[1] = 0 -> V_B[0] >= 1
 uvrfiA_half_dem_if_empty_1: A_empty[1] = 1 -> UVRFI_A[1] <= 2.1221e+07
 uvrfiB_half_dem_if_empty_1: B_empty[1] = 1 -> UVRFI_B[1] <= 5.325e+06
 Aempty1_2: A_empty[2] = 1 -> V_A[1] <= 1
 Aempty0_2: A_empty[2] = 0 -> V_A[1] >= 1
 Bempty1_2: B_empty[2] = 1 -> V_B[1] <= 1
 Bempty0_2: B_empty[2] = 0 -> V_B[1] >= 1
 uvrfiA_half_dem_if_empty_2: A_empty[2] = 1 -> UVRFI_A[2] <= 4.2442e+07
 uvrfiB_half_dem_if_empty_2: B_empty[2] = 1 -> UVRFI_B[2] <= 1.065e+07
 Aempty1_3: A_empty[3] = 1 -> V_A[2] <= 1
 Aempty0_3: A_empty[3] = 0 -> V_A[2] >= 1
 Bempty1_3: B_empty[3] = 1 -> V_B[2] <= 1
 Bempty0_3: B_empty[3] = 0 -> V_B[2] >= 1
 uvrfiA_half_dem_if_empty_3: A_empty[3] = 1 -> UVRFI_A[3] <= 6.3663e+07
 uvrfiB_half_dem_if_empty_3: B_empty[3] = 1 -> UVRFI_B[3] <= 1.5975e+07
 Aempty1_4: A_empty[4] = 1 -> V_A[3] <= 1
 Aempty0_4: A_empty[4] = 0 -> V_A[3] >= 1
 Bempty1_4: B_empty[4] = 1 -> V_B[3] <= 1
 Bempty0_4: B_empty[4] = 0 -> V_B[3] >= 1
 uvrfiA_half_dem_if_empty_4: A_empty[4] = 1 -> UVRFI_A[4] <= 8.4884e+07
 uvrfiB_half_dem_if_empty_4: B_empty[4] = 1 -> UVRFI_B[4] <= 2.13e+07
 Aempty1_5: A_empty[5] = 1 -> V_A[4] <= 1
 Aempty0_5: A_empty[5] = 0 -> V_A[4] >= 1
 Bempty1_5: B_empty[5] = 1 -> V_B[4] <= 1
 Bempty0_5: B_empty[5] = 0 -> V_B[4] >= 1
 uvrfiA_half_dem_if_empty_5: A_empty[5] = 1 -> UVRFI_A[5] <= 6.3663e+07
 uvrfiB_half_dem_if_empty_5: B_empty[5] = 1 -> UVRFI_B[5] <= 1.5975e+07
 Aempty1_6: A_empty[6] = 1 -> V_A[5] <= 1
 Aempty0_6: A_empty[6] = 0 -> V_A[5] >= 1
 Bempty1_6: B_empty[6] = 1 -> V_B[5] <= 1
 Bempty0_6: B_empty[6] = 0 -> V_B[5] >= 1
 uvrfiA_half_dem_if_empty_6: A_empty[6] = 1 -> UVRFI_A[6] <= 4.2442e+07
 uvrfiB_half_dem_if_empty_6: B_empty[6] = 1 -> UVRFI_B[6] <= 1.065e+07
 Aempty1_7: A_empty[7] = 1 -> V_A[6] <= 1
 Aempty0_7: A_empty[7] = 0 -> V_A[6] >= 1
 Bempty1_7: B_empty[7] = 1 -> V_B[6] <= 1
 Bempty0_7: B_empty[7] = 0 -> V_B[6] >= 1
 uvrfiA_half_dem_if_empty_7: A_empty[7] = 1 -> UVRFI_A[7] <= 2.1221e+07
 uvrfiB_half_dem_if_empty_7: B_empty[7] = 1 -> UVRFI_B[7] <= 5.325e+06
 Aempty1_8: A_empty[8] = 1 -> V_A[7] <= 1
 Aempty0_8: A_empty[8] = 0 -> V_A[7] >= 1
 Bempty1_8: B_empty[8] = 1 -> V_B[7] <= 1
 Bempty0_8: B_empty[8] = 0 -> V_B[7] >= 1
 uvrfiA_half_dem_if_empty_8: A_empty[8] = 1 -> UVRFI_A[8] <= 5.30525e+06
 uvrfiB_half_dem_if_empty_8: B_empty[8] = 1 -> UVRFI_B[8] <= 1.065e+06
 Aempty1_9: A_empty[9] = 1 -> V_A[8] <= 1
 Aempty0_9: A_empty[9] = 0 -> V_A[8] >= 1
 Bempty1_9: B_empty[9] = 1 -> V_B[8] <= 1
 Bempty0_9: B_empty[9] = 0 -> V_B[8] >= 1
 uvrfiA_half_dem_if_empty_9: A_empty[9] = 1 -> UVRFI_A[9] <= 0
 uvrfiB_half_dem_if_empty_9: B_empty[9] = 1 -> UVRFI_B[9] <= 0
 Aempty1_10: A_empty[10] = 1 -> V_A[9] <= 1
 Aempty0_10: A_empty[10] = 0 -> V_A[9] >= 1
 Bempty1_10: B_empty[10] = 1 -> V_B[9] <= 1
 Bempty0_10: B_empty[10] = 0 -> V_B[9] >= 1
 uvrfiA_half_dem_if_empty_10: A_empty[10] = 1 -> UVRFI_A[10] <= 0
 uvrfiB_half_dem_if_empty_10: B_empty[10] = 1 -> UVRFI_B[10] <= 0
 Aempty1_11: A_empty[11] = 1 -> V_A[10] <= 1
 Aempty0_11: A_empty[11] = 0 -> V_A[10] >= 1
 Bempty1_11: B_empty[11] = 1 -> V_B[10] <= 1
 Bempty0_11: B_empty[11] = 0 -> V_B[10] >= 1
 uvrfiA_half_dem_if_empty_11: A_empty[11] = 1 -> UVRFI_A[11] <= 0
 uvrfiB_half_dem_if_empty_11: B_empty[11] = 1 -> UVRFI_B[11] <= 0
Bounds
 V_R[0] <= 1.75e+08
 V_R[1] <= 1.75e+08
 V_R[2] <= 1.75e+08
 V_R[3] <= 1.75e+08
 V_R[4] <= 1.75e+08
 V_R[5] <= 1.75e+08
 V_R[6] <= 1.75e+08
 V_R[7] <= 1.75e+08
 V_R[8] <= 1.75e+08
 V_R[9] <= 1.75e+08
 V_R[10] <= 1.75e+08
 V_R[11] <= 1.75e+08
 V_A[0] <= 2.6e+08
 V_A[1] <= 2.6e+08
 V_A[2] <= 2.6e+08
 V_A[3] <= 2.6e+08
 V_A[4] <= 2.6e+08
 V_A[5] <= 2.6e+08
 V_A[6] <= 2.6e+08
 V_A[7] <= 2.6e+08
 V_A[8] <= 2.6e+08
 V_A[9] <= 2.6e+08
 V_A[10] <= 2.6e+08
 V_A[11] <= 2.6e+08
 V_B[0] <= 1.05e+08
 V_B[1] <= 1.05e+08
 V_B[2] <= 1.05e+08
 V_B[3] <= 1.05e+08
 V_B[4] <= 1.05e+08
 V_B[5] <= 1.05e+08
 V_B[6] <= 1.05e+08
 V_B[7] <= 1.05e+08
 V_B[8] <= 1.05e+08
 V_B[9] <= 1.05e+08
 V_B[10] <= 1.05e+08
 V_B[11] <= 1.05e+08
 tR[0] free
 tAB[0] free
 tmp_vrfi[0] free
 tR[1] free
 tAB[1] free
 tmp_vrfi[1] free
 tR[2] free
 tAB[2] free
 tmp_vrfi[2] free
 tR[3] free
 tAB[3] free
 tmp_vrfi[3] free
 tR[4] free
 tAB[4] free
 tmp_vrfi[4] free
 tR[5] free
 tAB[5] free
 tmp_vrfi[5] free
 tR[6] free
 tAB[6] free
 tmp_vrfi[6] free
 tR[7] free
 tAB[7] free
 tmp_vrfi[7] free
 tR[8] free
 tAB[8] free
 tmp_vrfi[8] free
 tR[9] free
 tAB[9] free
 tmp_vrfi[9] free
 tR[10] free
 tAB[10] free
 tmp_vrfi[10] free
 tR[11] free
 tAB[11] free
 tmp_vrfi[11] free
Binaries
 A_empty[0] A_empty[1] A_empty[2] A_empty[3] A_empty[4] A_empty[5]
 A_empty[6] A_empty[7] A_empty[8] A_empty[9] A_empty[10] A_empty[11]
 B_empty[0] B_empty[1] B_empty[2] B_empty[3] B_empty[4] B_empty[5]
 B_empty[6] B_empty[7] B_empty[8] B_empty[9] B_empty[10] B_empty[11]
General Constraints
 zR_max_0: zR[0] = MAX ( tR[0] , 0 )
 EB_cap_max_0: EB_cap[0] = MAX ( tAB[0] , 0 )
 yA_min_0: yA[0] = MIN ( shareA[0] , capA[0] )
 yB_min_0: yB[0] = MIN ( shareB[0] , capB[0] )
 VRFI_net_max_0: VRFI_net[0] = MAX ( tmp_vrfi[0] , 0 )
 minA_min_0: minA_req[0] = MIN ( auxA1[0] , auxA2[0] )
 minB_min_0: minB_req[0] = MIN ( auxB1[0] , auxB2[0] )
 zR_max_1: zR[1] = MAX ( tR[1] , 0 )
 EB_cap_max_1: EB_cap[1] = MAX ( tAB[1] , 0 )
 yA_min_1: yA[1] = MIN ( shareA[1] , capA[1] )
 yB_min_1: yB[1] = MIN ( shareB[1] , capB[1] )
 VRFI_net_max_1: VRFI_net[1] = MAX ( tmp_vrfi[1] , 0 )
 minA_min_1: minA_req[1] = MIN ( auxA1[1] , auxA2[1] )
 minB_min_1: minB_req[1] = MIN ( auxB1[1] , auxB2[1] )
 zR_max_2: zR[2] = MAX ( tR[2] , 0 )
 EB_cap_max_2: EB_cap[2] = MAX ( tAB[2] , 0 )
 yA_min_2: yA[2] = MIN ( shareA[2] , capA[2] )
 yB_min_2: yB[2] = MIN ( shareB[2] , capB[2] )
 VRFI_net_max_2: VRFI_net[2] = MAX ( tmp_vrfi[2] , 0 )
 minA_min_2: minA_req[2] = MIN ( auxA1[2] , auxA2[2] )
 minB_min_2: minB_req[2] = MIN ( auxB1[2] , auxB2[2] )
 zR_max_3: zR[3] = MAX ( tR[3] , 0 )
 EB_cap_max_3: EB_cap[3] = MAX ( tAB[3] , 0 )
 yA_min_3: yA[3] = MIN ( shareA[3] , capA[3] )
 yB_min_3: yB[3] = MIN ( shareB[3] , capB[3] )
 VRFI_net_max_3: VRFI_net[3] = MAX ( tmp_vrfi[3] , 0 )
 minA_min_3: minA_req[3] = MIN ( auxA1[3] , auxA2[3] )
 minB_min_3: minB_req[3] = MIN ( auxB1[3] , auxB2[3] )
 zR_max_4: zR[4] = MAX ( tR[4] , 0 )
 EB_cap_max_4: EB_cap[4] = MAX ( tAB[4] , 0 )
 yA_min_4: yA[4] = MIN ( shareA[4] , capA[4] )
 yB_min_4: yB[4] = MIN ( shareB[4] , capB[4] )
 VRFI_net_max_4: VRFI_net[4] = MAX ( tmp_vrfi[4] , 0 )
 minA_min_4: minA_req[4] = MIN ( auxA1[4] , auxA2[4] )
 minB_min_4: minB_req[4] = MIN ( auxB1[4] , auxB2[4] )
 zR_max_5: zR[5] = MAX ( tR[5] , 0 )
 EB_cap_max_5: EB_cap[5] = MAX ( tAB[5] , 0 )
 yA_min_5: yA[5] = MIN ( shareA[5] , capA[5] )
 yB_min_5: yB[5] = MIN ( shareB[5] , capB[5] )
 VRFI_net_max_5: VRFI_net[5] = MAX ( tmp_vrfi[5] , 0 )
 minA_min_5: minA_req[5] = MIN ( auxA1[5] , auxA2[5] )
 minB_min_5: minB_req[5] = MIN ( auxB1[5] , auxB2[5] )
 zR_max_6: zR[6] = MAX ( tR[6] , 0 )
 EB_cap_max_6: EB_cap[6] = MAX ( tAB[6] , 0 )
 yA_min_6: yA[6] = MIN ( shareA[6] , capA[6] )
 yB_min_6: yB[6] = MIN ( shareB[6] , capB[6] )
 VRFI_net_max_6: VRFI_net[6] = MAX ( tmp_vrfi[6] , 0 )
 minA_min_6: minA_req[6] = MIN ( auxA1[6] , auxA2[6] )
 minB_min_6: minB_req[6] = MIN ( auxB1[6] , auxB2[6] )
 zR_max_7: zR[7] = MAX ( tR[7] , 0 )
 EB_cap_max_7: EB_cap[7] = MAX ( tAB[7] , 0 )
 yA_min_7: yA[7] = MIN ( shareA[7] , capA[7] )
 yB_min_7: yB[7] = MIN ( shareB[7] , capB[7] )
 VRFI_net_max_7: VRFI_net[7] = MAX ( tmp_vrfi[7] , 0 )
 minA_min_7: minA_req[7] = MIN ( auxA1[7] , auxA2[7] )
 minB_min_7: minB_req[7] = MIN ( auxB1[7] , auxB2[7] )
 zR_max_8: zR[8] = MAX ( tR[8] , 0 )
 EB_cap_max_8: EB_cap[8] = MAX ( tAB[8] , 0 )
 yA_min_8: yA[8] = MIN ( shareA[8] , capA[8] )
 yB_min_8: yB[8] = MIN ( shareB[8] , capB[8] )
 VRFI_net_max_8: VRFI_net[8] = MAX ( tmp_vrfi[8] , 0 )
 minA_min_8: minA_req[8] = MIN ( auxA1[8] , auxA2[8] )
 minB_min_8: minB_req[8] = MIN ( auxB1[8] , auxB2[8] )
 zR_max_9: zR[9] = MAX ( tR[9] , 0 )
 EB_cap_max_9: EB_cap[9] = MAX ( tAB[9] , 0 )
 yA_min_9: yA[9] = MIN ( shareA[9] , capA[9] )
 yB_min_9: yB[9] = MIN ( shareB[9] , capB[9] )
 VRFI_net_max_9: VRFI_net[9] = MAX ( tmp_vrfi[9] , 0 )
 minA_min_9: minA_req[9] = MIN ( auxA1[9] , auxA2[9] )
 minB_min_9: minB_req[9] = MIN ( auxB1[9] , auxB2[9] )
 zR_max_10: zR[10] = MAX ( tR[10] , 0 )
 EB_cap_max_10: EB_cap[10] = MAX ( tAB[10] , 0 )
 yA_min_10: yA[10] = MIN ( shareA[10] , capA[10] )
 yB_min_10: yB[10] = MIN ( shareB[10] , capB[10] )
 VRFI_net_max_10: VRFI_net[10] = MAX ( tmp_vrfi[10] , 0 )
 minA_min_10: minA_req[10] = MIN ( auxA1[10] , auxA2[10] )
 minB_min_10: minB_req[10] = MIN ( auxB1[10] , auxB2[10] )
 zR_max_11: zR[11] = MAX ( tR[11] , 0 )
 EB_cap_max_11: EB_cap[11] = MAX ( tAB[11] , 0 )
 yA_min_11: yA[11] = MIN ( shareA[11] , capA[11] )
 yB_min_11: yB[11] = MIN ( shareB[11] , capB[11] )
 VRFI_net_max_11: VRFI_net[11] = MAX ( tmp_vrfi[11] , 0 )
 minA_min_11: minA_req[11] = MIN ( auxA1[11] , auxA2[11] )
 minB_min_11: minB_req[11] = MIN ( auxB1[11] , auxB2[11] )
End
